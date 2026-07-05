import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from media_manager.exceptions import ConflictError, NotFoundError

log = logging.getLogger(__name__)

T = TypeVar("T")
EntityId = UUID | int | str


class BaseRepository[T, S: BaseModel]:
    """
    Base repository providing common CRUD operations for media models.
    """

    def __init__(self, db: AsyncSession, model: type[T], schema: type[S]) -> None:
        self.db = db
        self.model = model
        self.schema = schema

    async def get_by_id(self, entity_id: EntityId) -> S:
        result = await self.db.get(self.model, entity_id)
        if not result:
            msg = f"{self.model.__name__} with id {entity_id} not found."
            raise NotFoundError(msg)
        return self.schema.model_validate(result)

    async def get_by_external_id(self, external_id: int, metadata_provider: str) -> S:
        stmt = select(self.model).where(
            self.model.external_id == external_id,
            self.model.metadata_provider == metadata_provider,
        )
        result = (await self.db.execute(stmt)).scalar_one_or_none()
        if not result:
            msg = f"{self.model.__name__} with external_id {external_id} and provider {metadata_provider} not found."
            raise NotFoundError(msg)
        return self.schema.model_validate(result)

    async def get_all(self) -> list[S]:
        stmt = select(self.model)
        results = (await self.db.execute(stmt)).scalars().unique().all()
        return [self.schema.model_validate(r) for r in results]

    async def delete(self, entity_id: EntityId) -> None:
        obj = await self.db.get(self.model, entity_id)
        if not obj:
            msg = f"{self.model.__name__} with id {entity_id} not found."
            raise NotFoundError(msg)
        await self.db.delete(obj)
        await self.db.commit()

    async def set_library(self, entity_id: EntityId, library: str) -> None:
        obj = await self.db.get(self.model, entity_id)
        if not obj:
            msg = f"{self.model.__name__} with id {entity_id} not found."
            raise NotFoundError(msg)
        obj.library = library
        await self.db.commit()

    async def save_media_base(
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

        db_obj = (
            await self.db.get(model_class, media_schema.id) if media_schema.id else None
        )

        if db_obj:
            update_exclude = exclude | {"id"}
            for key, value in media_schema.model_dump(exclude=update_exclude).items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
        else:
            db_obj = model_class(**media_schema.model_dump(exclude=exclude))
            self.db.add(db_obj)

        try:
            await self.db.commit()
            await self.db.refresh(db_obj)
        except IntegrityError as e:
            await self.db.rollback()
            msg = f"Integrity error while saving {model_class.__name__}: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            await self.db.rollback()
            log.exception(f"Database error while saving {model_class.__name__}")
            raise
        else:
            return self.schema.model_validate(db_obj)

    async def update_media_attributes_base(
        self,
        media_id: EntityId,
        model_class: type[T],
        **attributes: Any,  # noqa: ANN401
    ) -> S:
        """
        Generic update method for media attributes.
        """
        db_obj = await self.db.get(model_class, media_id)
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
                await self.db.commit()
                await self.db.refresh(db_obj)
            except SQLAlchemyError:
                await self.db.rollback()
                raise

        return self.schema.model_validate(db_obj)

    async def add_media_file_base(
        self, file_schema: S, model_class: type[T], schema_class: type[S]
    ) -> S:
        """
        Generic method to add a media file record.
        """
        db_model = model_class(**file_schema.model_dump())
        try:
            self.db.add(db_model)
            await self.db.commit()
            await self.db.refresh(db_model)
        except IntegrityError:
            await self.db.rollback()
            raise
        except SQLAlchemyError:
            await self.db.rollback()
            raise
        else:
            return schema_class.model_validate(db_model)

    async def remove_files_by_torrent_id_base(
        self, torrent_id: EntityId, model_class: type[T]
    ) -> int:
        """
        Generic method to remove media files by torrent ID.
        """
        try:
            stmt = delete(model_class).where(model_class.torrent_id == torrent_id)
            result = await self.db.execute(stmt)
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise
        else:
            return result.rowcount
