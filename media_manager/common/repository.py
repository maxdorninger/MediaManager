import logging
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from media_manager.exceptions import ConflictError, NotFoundError

log = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")
EntityId = UUID | int | str


class BaseRepository[T, S]:
    """
    Base repository providing common CRUD operations for media models.
    """

    def __init__(self, db: Session, model: type[T], schema: type[S]) -> None:
        self.db = db
        self.model = model
        self.schema = schema

    def get_by_id(self, entity_id: EntityId) -> S:
        result = self.db.get(self.model, entity_id)
        if not result:
            msg = f"{self.model.__name__} with id {entity_id} not found."
            raise NotFoundError(msg)
        return self.schema.model_validate(result)

    def get_by_external_id(self, external_id: int, metadata_provider: str) -> S:
        stmt = select(self.model).where(
            self.model.external_id == external_id,
            self.model.metadata_provider == metadata_provider,
        )
        result = self.db.execute(stmt).scalar_one_or_none()
        if not result:
            msg = f"{self.model.__name__} with external_id {external_id} and provider {metadata_provider} not found."
            raise NotFoundError(msg)
        return self.schema.model_validate(result)

    def get_all(self) -> list[S]:
        stmt = select(self.model)
        results = self.db.execute(stmt).scalars().unique().all()
        return [self.schema.model_validate(r) for r in results]

    def delete(self, entity_id: EntityId) -> None:
        obj = self.db.get(self.model, entity_id)
        if not obj:
            msg = f"{self.model.__name__} with id {entity_id} not found."
            raise NotFoundError(msg)
        self.db.delete(obj)
        self.db.commit()

    def set_library(self, entity_id: EntityId, library: str) -> None:
        obj = self.db.get(self.model, entity_id)
        if not obj:
            msg = f"{self.model.__name__} with id {entity_id} not found."
            raise NotFoundError(msg)
        obj.library = library
        self.db.commit()

    def save_media_base(
        self,
        media_schema: S,
        model_class: type[T],
        exclude: set[str] | None = None,
    ) -> S:
        """
        Generic save method for media models.
        """
        if exclude is None:
            exclude = set()

        db_obj = self.db.get(model_class, media_schema.id) if media_schema.id else None

        if db_obj:
            # Update existing
            # Always exclude "id" from updates
            update_exclude = exclude | {"id"}
            for key, value in media_schema.model_dump(exclude=update_exclude).items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
        else:
            # Insert new
            db_obj = model_class(**media_schema.model_dump(exclude=exclude))
            self.db.add(db_obj)

        try:
            self.db.commit()
            self.db.refresh(db_obj)
        except IntegrityError as e:
            self.db.rollback()
            msg = f"Integrity error while saving {model_class.__name__}: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while saving {model_class.__name__}")
            raise
        else:
            return self.schema.model_validate(db_obj)

    def update_media_attributes_base(
        self,
        media_id: EntityId,
        model_class: type[T],
        **attributes: Any,  # noqa: ANN401
    ) -> S:
        """
        Generic update method for media attributes.
        """
        db_obj = self.db.get(model_class, media_id)
        if not db_obj:
            msg = f"{model_class.__name__} with id {media_id} not found."
            raise NotFoundError(msg)

        updated = False
        for key, value in attributes.items():
            if (
                value is not None
                and hasattr(db_obj, key)
                and getattr(db_obj, key) != value
            ):
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

    def add_media_file_base(
        self, file_schema: S, model_class: type[T], schema_class: type[S]
    ) -> S:
        """
        Generic method to add a media file record.
        """
        db_model = model_class(**file_schema.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
        except IntegrityError:
            self.db.rollback()
            raise
        except SQLAlchemyError:
            self.db.rollback()
            raise
        else:
            return schema_class.model_validate(db_model)

    def remove_files_by_torrent_id_base(
        self, torrent_id: EntityId, model_class: type[T]
    ) -> int:
        """
        Generic method to remove media files by torrent ID.
        """
        try:
            stmt = delete(model_class).where(model_class.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        else:
            return result.rowcount
