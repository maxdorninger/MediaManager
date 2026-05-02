from typing import Annotated

from fastapi import Depends, HTTPException, Path

from media_manager.database import DbSessionDependency
from media_manager.exceptions import NotFoundError
from media_manager.indexer.dependencies import indexer_service_dep
from media_manager.notification.dependencies import notification_service_dep
from media_manager.torrent.dependencies import torrent_service_dep
from media_manager.tv.importer import TvImportService
from media_manager.tv.metadata import TvMetadataService
from media_manager.tv.repository import TvRepository
from media_manager.tv.schemas import Season, SeasonId, Show, ShowId
from media_manager.tv.service import TvService


def get_tv_repository(db_session: DbSessionDependency) -> TvRepository:
    return TvRepository(db_session)


tv_repository_dep = Annotated[TvRepository, Depends(get_tv_repository)]


def get_tv_metadata_service(
    tv_repository: tv_repository_dep,
) -> TvMetadataService:
    return TvMetadataService(tv_repository=tv_repository)


tv_metadata_service_dep = Annotated[TvMetadataService, Depends(get_tv_metadata_service)]


def get_tv_import_service(
    tv_repository: tv_repository_dep,
    torrent_service: torrent_service_dep,
    notification_service: notification_service_dep,
    tv_metadata_service: tv_metadata_service_dep,
) -> TvImportService:
    return TvImportService(
        tv_repository=tv_repository,
        torrent_service=torrent_service,
        notification_service=notification_service,
        tv_metadata_service=tv_metadata_service,
    )


tv_import_service_dep = Annotated[TvImportService, Depends(get_tv_import_service)]


def get_tv_service(
    tv_repository: tv_repository_dep,
    torrent_service: torrent_service_dep,
    indexer_service: indexer_service_dep,
    notification_service: notification_service_dep,
    tv_import_service: tv_import_service_dep,
    tv_metadata_service: tv_metadata_service_dep,
) -> TvService:
    return TvService(
        tv_repository=tv_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
        notification_service=notification_service,
        tv_import_service=tv_import_service,
        tv_metadata_service=tv_metadata_service,
    )


tv_service_dep = Annotated[TvService, Depends(get_tv_service)]


def get_show_by_id(
    tv_service: tv_service_dep,
    show_id: ShowId = Path(..., description="The ID of the show"),
) -> Show:
    try:
        show = tv_service.get_show_by_id(show_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Show with ID {show_id} not found.",
        ) from None
    return show


show_dep = Annotated[Show, Depends(get_show_by_id)]


def get_season_by_id(
    tv_service: tv_service_dep,
    season_id: SeasonId = Path(..., description="The ID of the season"),
) -> Season:
    try:
        season = tv_service.get_season(season_id=season_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Season with ID {season_id} not found.",
        ) from None
    return season


season_dep = Annotated[Season, Depends(get_season_by_id)]
