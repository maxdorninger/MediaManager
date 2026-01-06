from typing import Annotated

from fastapi import Depends

from media_manager.database import DbSessionDependency
from media_manager.indexer.repository import IndexerRepository
from media_manager.indexer.service import IndexerService


def get_indexer_repository(db_session: DbSessionDependency) -> IndexerRepository:
    return IndexerRepository(db_session)


indexer_repository_dep = Annotated[IndexerRepository, Depends(get_indexer_repository)]


def get_indexer_service(
    indexer_repository: indexer_repository_dep,
) -> IndexerService:
    return IndexerService(indexer_repository)


indexer_service_dep = Annotated[IndexerService, Depends(get_indexer_service)]
