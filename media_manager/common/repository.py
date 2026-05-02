import logging
from typing import Generic, Type, TypeVar, List, Any
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from media_manager.exceptions import NotFoundError

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
