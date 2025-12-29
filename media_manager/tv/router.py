from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException

from media_manager.auth.db import User
from media_manager.auth.schemas import UserRead
from media_manager.auth.users import current_active_user, current_superuser
from media_manager.config import AllEncompassingConfig, LibraryItem
from media_manager.exceptions import MediaAlreadyExists
from media_manager.indexer.schemas import (
    IndexerQueryResultId,
    IndexerQueryResult,
)
from media_manager.metadataProvider.dependencies import metadata_provider_dep
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.schemas import Torrent
from media_manager.torrent.utils import get_importable_media_directories
from media_manager.tv import log
from media_manager.tv.dependencies import (
    season_dep,
    show_dep,
    tv_service_dep,
)
from media_manager.tv.schemas import (
    Show,
    SeasonRequest,
    ShowId,
    RichShowTorrent,
    PublicShow,
    PublicSeasonFile,
    CreateSeasonRequest,
    SeasonRequestId,
    UpdateSeasonRequest,
    RichSeasonRequest,
    Season,
)

router = APIRouter()

# -----------------------------------------------------------------------------
# METADATA & SEARCH
# -----------------------------------------------------------------------------

@router.get(
    "/search",
    dependencies=[Depends(current_active_user)],
    response_model=list[MetaDataProviderSearchResult],
)
def search_metadata_providers_for_a_show(
        tv_service: tv_service_dep, query: str, metadata_provider: metadata_provider_dep
):
    """
    Search for a show on the configured metadata provider.
    """
    return tv_service.search_for_show(query=query, metadata_provider=metadata_provider)


@router.get(
    "/recommended",
    dependencies=[Depends(current_active_user)],
    response_model=list[MetaDataProviderSearchResult],
)
def get_recommended_shows(
        tv_service: tv_service_dep, metadata_provider: metadata_provider_dep
):
    """
    Get a list of recommended/popular shows from the metadata provider.
    """
    return tv_service.get_popular_shows(metadata_provider=metadata_provider)


# -----------------------------------------------------------------------------
# IMPORTING
# -----------------------------------------------------------------------------

@router.get(
    "/importable",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
    response_model=list[MediaImportSuggestion],
)
def get_all_importable_shows(
        tv_service: tv_service_dep, metadata_provider: metadata_provider_dep
):
    """
    Get a list of unknown shows that were detected in the TV directory and are importable.
    """
    return tv_service.get_importable_tv_shows(metadata_provider=metadata_provider)


@router.post(
    "/importable/{show_id}",
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_204_NO_CONTENT,
)
def import_detected_show(tv_service: tv_service_dep, tv_show: show_dep, directory: str):
    """
    Import a detected show from the specified directory into the library.
    """
    source_directory = Path(directory)
    if source_directory not in get_importable_media_directories(
            AllEncompassingConfig().misc.tv_directory
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No such directory")
    tv_service.import_existing_tv_show(
        tv_show=tv_show, source_directory=source_directory
    )


# -----------------------------------------------------------------------------
# SHOWS
# -----------------------------------------------------------------------------

@router.get(
    "/shows",
    dependencies=[Depends(current_active_user)],
    response_model=list[Show]
)
def get_all_shows(tv_service: tv_service_dep):
    """
    Get all shows in the library.
    """
    return tv_service.get_all_shows()


@router.post(
    "/shows",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_201_CREATED: {
            "model": Show,
            "description": "Successfully created show",
        }
    },
)
def add_a_show(
        tv_service: tv_service_dep,
        metadata_provider: metadata_provider_dep,
        show_id: int,
        language: str | None = None,
):
    """
    Add a new show to the library.
    """
    try:
        show = tv_service.add_show(
            external_id=show_id,
            metadata_provider=metadata_provider,
            language=language,
        )
    except MediaAlreadyExists:
        show = tv_service.get_show_by_external_id(
            show_id, metadata_provider=metadata_provider.name
        )
    return show


@router.get(
    "/shows/torrents",
    dependencies=[Depends(current_active_user)],
    response_model=list[RichShowTorrent],
)
def get_shows_with_torrents(tv_service: tv_service_dep):
    """
    Get all shows that are associated with torrents.
    """
    result = tv_service.get_all_shows_with_torrents()
    return result


@router.get(
    "/shows/libraries",
    dependencies=[Depends(current_active_user)],
    response_model=list[LibraryItem],
)
def get_available_libraries():
    """
    Get available TV libraries from configuration.
    """
    return AllEncompassingConfig().misc.tv_libraries


# -----------------------------------------------------------------------------
# SHOWS - INDIVIDUAL
# -----------------------------------------------------------------------------

@router.get(
    "/shows/{show_id}",
    dependencies=[Depends(current_active_user)],
    response_model=PublicShow,
)
def get_a_show(show: show_dep, tv_service: tv_service_dep) -> PublicShow:
    """
    Get details for a specific show.
    """
    return tv_service.get_public_show_by_id(show_id=show.id)


@router.delete(
    "/shows/{show_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_a_show(
        tv_service: tv_service_dep,
        show: show_dep,
        delete_files_on_disk: bool = False,
        delete_torrents: bool = False,
):
    """
    Delete a show from the library.
    """
    tv_service.delete_show(
        show_id=show.id,
        delete_files_on_disk=delete_files_on_disk,
        delete_torrents=delete_torrents,
    )


@router.post(
    "/shows/{show_id}/metadata",
    dependencies=[Depends(current_active_user)],
    response_model=PublicShow,
)
def update_shows_metadata(
        show: show_dep, tv_service: tv_service_dep, metadata_provider: metadata_provider_dep
) -> PublicShow:
    """
    Update a show's metadata from the provider.
    """
    tv_service.update_show_metadata(db_show=show, metadata_provider=metadata_provider)
    return tv_service.get_public_show_by_id(show_id=show.id)


@router.post(
    "/shows/{show_id}/continuousDownload",
    dependencies=[Depends(current_superuser)],
    response_model=PublicShow,
)
def set_continuous_download(
        show: show_dep, tv_service: tv_service_dep, continuous_download: bool
) -> PublicShow:
    """
    Toggle whether future seasons of a show will be automatically downloaded.
    """
    tv_service.set_show_continuous_download(
        show_id=show.id, continuous_download=continuous_download
    )
    return tv_service.get_public_show_by_id(show_id=show.id)


@router.post(
    "/shows/{show_id}/library",
    dependencies=[Depends(current_superuser)],
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_library(
        show: show_dep,
        tv_service: tv_service_dep,
        library: str,
) -> None:
    """
    Set the library path for a Show.
    """
    tv_service.set_show_library(show_id=show.id, library=library)
    return


@router.get(
    "/shows/{show_id}/torrents",
    dependencies=[Depends(current_active_user)],
    response_model=RichShowTorrent,
)
def get_a_shows_torrents(show: show_dep, tv_service: tv_service_dep):
    """
    Get torrents associated with a specific show.
    """
    return tv_service.get_torrents_for_show(show=show)


# -----------------------------------------------------------------------------
# SEASONS - REQUESTS
# -----------------------------------------------------------------------------

@router.get(
    "/seasons/requests",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_active_user)],
    response_model=list[RichSeasonRequest],
)
def get_season_requests(tv_service: tv_service_dep) -> list[RichSeasonRequest]:
    """
    Get all season requests.
    """
    return tv_service.get_all_season_requests()


@router.post("/seasons/requests", status_code=status.HTTP_204_NO_CONTENT)
def request_a_season(
        user: Annotated[User, Depends(current_active_user)],
        season_request: CreateSeasonRequest,
        tv_service: tv_service_dep,
):
    """
    Create a new season request.
    """
    request: SeasonRequest = SeasonRequest.model_validate(season_request)
    request.requested_by = UserRead.model_validate(user)
    if user.is_superuser:
        request.authorized = True
        request.authorized_by = UserRead.model_validate(user)
    tv_service.add_season_request(request)
    return


@router.put("/seasons/requests", status_code=status.HTTP_204_NO_CONTENT)
def update_request(
        tv_service: tv_service_dep,
        user: Annotated[User, Depends(current_active_user)],
        season_request: UpdateSeasonRequest,
):
    """
    Update an existing season request.
    """
    updated_season_request: SeasonRequest = SeasonRequest.model_validate(season_request)
    request = tv_service.get_season_request_by_id(
        season_request_id=updated_season_request.id
    )
    if request.requested_by.id == user.id or user.is_superuser:
        updated_season_request.requested_by = UserRead.model_validate(user)
        tv_service.update_season_request(season_request=updated_season_request)
    return


@router.patch(
    "/seasons/requests/{season_request_id}", status_code=status.HTTP_204_NO_CONTENT
)
def authorize_request(
        tv_service: tv_service_dep,
        user: Annotated[User, Depends(current_superuser)],
        season_request_id: SeasonRequestId,
        authorized_status: bool = False,
):
    """
    Authorize or de-authorize a season request.
    """
    season_request = tv_service.get_season_request_by_id(
        season_request_id=season_request_id
    )
    season_request.authorized_by = UserRead.model_validate(user)
    season_request.authorized = authorized_status
    if not authorized_status:
        season_request.authorized_by = None
    tv_service.update_season_request(season_request=season_request)
    return


@router.delete(
    "/seasons/requests/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_season_request(
        tv_service: tv_service_dep,
        user: Annotated[User, Depends(current_active_user)],
        request_id: SeasonRequestId,
):
    """
    Delete a season request.
    """
    request = tv_service.get_season_request_by_id(season_request_id=request_id)
    if user.is_superuser or request.requested_by.id == user.id:
        tv_service.delete_season_request(season_request_id=request_id)
        log.info(f"User {user.id} deleted season request {request_id}.")
        return None
    else:
        log.warning(
            f"User {user.id} tried to delete season request {request_id} but is not authorized."
        )
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this request",
        )


# -----------------------------------------------------------------------------
# SEASONS
# -----------------------------------------------------------------------------

@router.get(
    "/seasons/{season_id}",
    dependencies=[Depends(current_active_user)],
    response_model=Season,
)
def get_season(season: season_dep) -> Season:
    """
    Get details for a specific season.
    """
    return season


@router.get(
    "/seasons/{season_id}/files",
    dependencies=[Depends(current_active_user)],
    response_model=list[PublicSeasonFile],
)
def get_season_files(
        season: season_dep, tv_service: tv_service_dep
) -> list[PublicSeasonFile]:
    """
    Get files associated with a specific season.
    """
    return tv_service.get_public_season_files_by_season_id(season_id=season.id)


# -----------------------------------------------------------------------------
# TORRENTS
# -----------------------------------------------------------------------------

@router.get(
    "/torrents",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
    response_model=list[IndexerQueryResult],
)
def get_torrents_for_a_season(
        tv_service: tv_service_dep,
        show_id: ShowId,
        season_number: int = 1,
        search_query_override: str = None,
):
    """
    Search for torrents for a specific season of a show.
    Default season_number is 1 because it often returns multi-season torrents.
    """
    return tv_service.get_all_available_torrents_for_a_season(
        season_number=season_number,
        show_id=show_id,
        search_query_override=search_query_override,
    )


@router.post(
    "/torrents",
    status_code=status.HTTP_200_OK,
    response_model=Torrent,
    dependencies=[Depends(current_superuser)],
)
def download_a_torrent(
        tv_service: tv_service_dep,
        public_indexer_result_id: IndexerQueryResultId,
        show_id: ShowId,
        override_file_path_suffix: str = "",
):
    """
    Trigger a download for a specific torrent.
    """
    return tv_service.download_torrent(
        public_indexer_result_id=public_indexer_result_id,
        show_id=show_id,
        override_show_file_path_suffix=override_file_path_suffix,
    )


# -----------------------------------------------------------------------------
# STATISTICS
# -----------------------------------------------------------------------------

@router.get(
    "/episodes/count",
    status_code=status.HTTP_200_OK,
    response_model=int,
    description="Total number of episodes downloaded",
    dependencies=[Depends(current_active_user)],
)
def get_total_count_of_downloaded_episodes(tv_service: tv_service_dep):
    """
    Get the total count of downloaded episodes across all shows.
    """
    return tv_service.get_total_downloaded_episoded_count()
