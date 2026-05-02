import logging
from typing import Generic, Type, TypeVar, List, Any, Optional
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from media_manager.exceptions import NotFoundError, ConflictError

log = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")

class BaseRepository(Generic[T, S]):
    """
    Base repository providing common CRUD operations for media models.
    """
    def __init__(self, db: Session, model: Type[T], schema: Type[S]) -> None:
        self.db = db
        self.model = model
        self.schema = schema

    def get_by_id(self, id: Any) -> S:
        result = self.db.get(self.model, id)
        if not result:
            msg = f"{self.model.__name__} with id {id} not found."
            raise NotFoundError(msg)
        return self.schema.model_validate(result)

    def get_by_external_id(self, external_id: int, metadata_provider: str) -> S:
        stmt = select(self.model).where(
            self.model.external_id == external_id,
            self.model.metadata_provider == metadata_provider
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        if not result:
            msg = f"{self.model.__name__} with external_id {external_id} and provider {metadata_provider} not found."
            raise NotFoundError(msg)
        return self.schema.model_validate(result)

    def get_all(self) -> List[S]:
        stmt = select(self.model)
        results = self.db.execute(stmt).scalars().unique().all()
        return [self.schema.model_validate(r) for r in results]

    def delete(self, id: Any) -> None:
        obj = self.db.get(self.model, id)
        if not obj:
            msg = f"{self.model.__name__} with id {id} not found."
            raise NotFoundError(msg)
        self.db.delete(obj)
        self.db.commit()

    def set_library(self, id: Any, library: str) -> None:
        obj = self.db.get(self.model, id)
        if not obj:
            msg = f"{self.model.__name__} with id {id} not found."
            raise NotFoundError(msg)
        obj.library = library
        self.db.commit()

    def save_media_base(self, media_schema: Any, model_class: Type[Any]) -> S:
        """
        Generic save method for media models.
        """
        db_obj = self.db.get(model_class, media_schema.id) if media_schema.id else None

        if db_obj:
            # Update existing
            for key, value in media_schema.model_dump(exclude={"id", "seasons", "episodes"}).items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
        else:
            # Insert new
            # Note: Complex nested objects like Seasons/Episodes might need specialized handling in subclasses
            # but for Movie it works directly.
            db_obj = model_class(**media_schema.model_dump(exclude={"seasons", "episodes"}))
            self.db.add(db_obj)

        try:
            self.db.commit()
            self.db.refresh(db_obj)
            return self.schema.model_validate(db_obj)
        except IntegrityError as e:
            self.db.rollback()
            msg = f"Integrity error while saving {model_class.__name__}: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while saving {model_class.__name__}")
            raise

    def update_media_attributes_base(self, media_id: Any, model_class: Type[Any], **attributes) -> S:
        """
        Generic update method for media attributes.
        """
        db_obj = self.db.get(model_class, media_id)
        if not db_obj:
            msg = f"{model_class.__name__} with id {media_id} not found."
            raise NotFoundError(msg)

        updated = False
        for key, value in attributes.items():
            if value is not None and hasattr(db_obj, key) and getattr(db_obj, key) != value:
                setattr(db_obj, key, value)
                updated = True

        if updated:
            try:
                self.db.commit()
                self.db.refresh(db_obj)
            except SQLAlchemyError:
                self.db.rollback()
                raise
        
        return self.schema.model_validate(db_obj)

    def add_media_file_base(self, file_schema: Any, model_class: Type[Any], schema_class: Type[Any]) -> Any:
        """
        Generic method to add a media file record.
        """
        db_model = model_class(**file_schema.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            return schema_class.model_validate(db_model)
        except IntegrityError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def remove_files_by_torrent_id_base(self, torrent_id: Any, model_class: Type[Any]) -> int:
        """
        Generic method to remove media files by torrent ID.
        """
        try:
            stmt = delete(model_class).where(model_class.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
            return result.rowcount
        except SQLAlchemyError:
            self.db.rollback()
            raise
