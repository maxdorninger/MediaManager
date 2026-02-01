from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from media_manager.auth.schemas import UserRead
from media_manager.auth.users import current_active_user, current_superuser
from media_manager.config import LibraryItem, MediaManagerConfig
from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.indexer.schemas import (
    IndexerQueryResult,
    IndexerQueryResultId,
)
from media_manager.metadataProvider.dependencies import metadata_provider_dep
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.movies import log
from media_manager.movies.dependencies import (
    movie_dep,
    movie_service_dep,
)
from media_manager.movies.schemas import (
    CreateMovieRequest,
    Movie,
    MovieRequest,
    MovieRequestBase,
    MovieRequestId,
    PublicMovie,
    PublicMovieFile,
    RichMovieRequest,
    RichMovieTorrent,
)
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.schemas import Torrent
from media_manager.torrent.utils import get_importable_media_directories

router = APIRouter()

# -----------------------------------------------------------------------------
# METADATA & SEARCH
# -----------------------------------------------------------------------------


@router.get(
    "/search",
    dependencies=[Depends(current_active_user)],
)
def search_for_movie(
    query: str,
    movie_service: movie_service_dep,
    metadata_provider: metadata_provider_dep,
) -> list[MetaDataProviderSearchResult]:
    """
    Search for a movie on the configured metadata provider.
    """
    return movie_service.search_for_movie(
        query=query, metadata_provider=metadata_provider
    )


@router.get(
    "/recommended",
    dependencies=[Depends(current_active_user)],
)
def get_popular_movies(
    movie_service: movie_service_dep,
    metadata_provider: metadata_provider_dep,
) -> list[MetaDataProviderSearchResult]:
    """
    Get a list of recommended/popular movies from the metadata provider.
    """
    return movie_service.get_popular_movies(metadata_provider=metadata_provider)


# -----------------------------------------------------------------------------
# IMPORTING
# -----------------------------------------------------------------------------


@router.get(
    "/importable",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
)
def get_all_importable_movies(
    movie_service: movie_service_dep, metadata_provider: metadata_provider_dep
) -> list[MediaImportSuggestion]:
    """
    Get a list of unknown movies that were detected in the movie directory and are importable.
    """
    return movie_service.get_importable_movies(metadata_provider=metadata_provider)


@router.post(
    "/importable/{movie_id}",
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_204_NO_CONTENT,
)
def import_detected_movie(
    movie_service: movie_service_dep, movie: movie_dep, directory: str
) -> None:
    """
    Import a detected movie from the specified directory into the library.
    """
    source_directory = Path(directory)
    if source_directory not in get_importable_media_directories(
        MediaManagerConfig().misc.movie_directory
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No such directory")
    success = movie_service.import_existing_movie(
        movie=movie, source_directory=source_directory
    )
    if not success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Error on importing")


# -----------------------------------------------------------------------------
# MOVIES
# -----------------------------------------------------------------------------


@router.get(
    "",
    dependencies=[Depends(current_active_user)],
)
def get_all_movies(movie_service: movie_service_dep) -> list[Movie]:
    """
    Get all movies in the library.
    """
    return movie_service.get_all_movies()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_201_CREATED: {
            "model": Movie,
            "description": "Successfully created movie",
        }
    },
)
def add_a_movie(
    movie_service: movie_service_dep,
    metadata_provider: metadata_provider_dep,
    movie_id: int,
    language: str | None = None,
) -> Movie:
    """
    Add a new movie to the library.
    """
    try:
        movie = movie_service.add_movie(
            external_id=movie_id,
            metadata_provider=metadata_provider,
            language=language,
        )
    except ConflictError:
        movie = movie_service.get_movie_by_external_id(
            external_id=movie_id, metadata_provider=metadata_provider.name
        )
        if not movie:
            raise NotFoundError from ConflictError
    return movie


@router.get(
    "/torrents",
    dependencies=[Depends(current_active_user)],
)
def get_all_movies_with_torrents(
    movie_service: movie_service_dep,
) -> list[RichMovieTorrent]:
    """
    Get all movies that are associated with torrents.
    """
    return movie_service.get_all_movies_with_torrents()


@router.get(
    "/libraries",
    dependencies=[Depends(current_active_user)],
)
def get_available_libraries() -> list[LibraryItem]:
    """
    Get available Movie libraries from configuration.
    """
    return MediaManagerConfig().misc.movie_libraries


# -----------------------------------------------------------------------------
# MOVIE REQUESTS
# -----------------------------------------------------------------------------


@router.get(
    "/requests",
    dependencies=[Depends(current_active_user)],
)
def get_all_movie_requests(movie_service: movie_service_dep) -> list[RichMovieRequest]:
    """
    Get all movie requests.
    """
    return movie_service.get_all_movie_requests()


@router.post(
    "/requests",
    status_code=status.HTTP_201_CREATED,
)
def create_movie_request(
    movie_service: movie_service_dep,
    movie_request: CreateMovieRequest,
    user: Annotated[UserRead, Depends(current_active_user)],
) -> MovieRequest:
    """
    Create a new movie request.
    """
    log.info(
        f"User {user.email} is creating a movie request for {movie_request.movie_id}"
    )
    movie_request: MovieRequest = MovieRequest.model_validate(movie_request)
    movie_request.requested_by = user
    if user.is_superuser:
        movie_request.authorized = True
        movie_request.authorized_by = user

    return movie_service.add_movie_request(movie_request=movie_request)


@router.put(
    "/requests/{movie_request_id}",
)
def update_movie_request(
    movie_service: movie_service_dep,
    movie_request_id: MovieRequestId,
    update_movie_request: MovieRequestBase,
    user: Annotated[UserRead, Depends(current_active_user)],
) -> MovieRequest:
    """
    Update an existing movie request.
    """
    movie_request = movie_service.get_movie_request_by_id(
        movie_request_id=movie_request_id
    )
    if movie_request.requested_by.id != user.id or user.is_superuser:
        movie_request.min_quality = update_movie_request.min_quality
        movie_request.wanted_quality = update_movie_request.wanted_quality

    return movie_service.update_movie_request(movie_request=movie_request)


@router.patch("/requests/{movie_request_id}", status_code=status.HTTP_204_NO_CONTENT)
def authorize_request(
    movie_service: movie_service_dep,
    movie_request_id: MovieRequestId,
    user: Annotated[UserRead, Depends(current_superuser)],
    authorized_status: bool = False,
) -> None:
    """
    Authorize or de-authorize a movie request.
    """
    movie_request = movie_service.get_movie_request_by_id(
        movie_request_id=movie_request_id
    )
    movie_request.authorized = authorized_status
    if authorized_status:
        movie_request.authorized_by = user
    else:
        movie_request.authorized_by = None
    movie_service.update_movie_request(movie_request=movie_request)


@router.delete(
    "/requests/{movie_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_movie_request(
    movie_service: movie_service_dep, movie_request_id: MovieRequestId
) -> None:
    """
    Delete a movie request.
    """
    movie_service.delete_movie_request(movie_request_id=movie_request_id)


# -----------------------------------------------------------------------------
# MOVIES - SINGLE RESOURCE
# -----------------------------------------------------------------------------


@router.get(
    "/{movie_id}",
    dependencies=[Depends(current_active_user)],
)
def get_movie_by_id(movie_service: movie_service_dep, movie: movie_dep) -> PublicMovie:
    """
    Get details for a specific movie.
    """
    return movie_service.get_public_movie_by_id(movie=movie)


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_a_movie(
    movie_service: movie_service_dep,
    movie: movie_dep,
    delete_files_on_disk: bool = False,
    delete_torrents: bool = False,
) -> None:
    """
    Delete a movie from the library.
    """
    movie_service.delete_movie(
        movie=movie,
        delete_files_on_disk=delete_files_on_disk,
        delete_torrents=delete_torrents,
    )


@router.post(
    "/{movie_id}/library",
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_library(
    movie: movie_dep,
    movie_service: movie_service_dep,
    library: str,
) -> None:
    """
    Set the library path for a Movie.
    """
    movie_service.set_movie_library(movie=movie, library=library)
    return


@router.get(
    "/{movie_id}/files",
    dependencies=[Depends(current_active_user)],
)
def get_movie_files_by_movie_id(
    movie_service: movie_service_dep, movie: movie_dep
) -> list[PublicMovieFile]:
    """
    Get files associated with a specific movie.
    """
    return movie_service.get_public_movie_files(movie=movie)


@router.get(
    "/{movie_id}/torrents",
    dependencies=[Depends(current_active_user)],
)
def search_for_torrents_for_movie(
    movie_service: movie_service_dep,
    movie: movie_dep,
    search_query_override: str | None = None,
) -> list[IndexerQueryResult]:
    """
    Search for torrents for a specific movie.
    """
    return movie_service.get_all_available_torrents_for_movie(
        movie=movie, search_query_override=search_query_override
    )


@router.post(
    "/{movie_id}/torrents",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
)
def download_torrent_for_movie(
    movie_service: movie_service_dep,
    movie: movie_dep,
    public_indexer_result_id: IndexerQueryResultId,
    override_file_path_suffix: str = "",
) -> Torrent:
    """
    Trigger a download for a specific torrent for a movie.
    """
    return movie_service.download_torrent(
        public_indexer_result_id=public_indexer_result_id,
        movie=movie,
        override_movie_file_path_suffix=override_file_path_suffix,
    )
