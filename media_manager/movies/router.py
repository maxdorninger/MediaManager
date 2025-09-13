from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from media_manager.auth.schemas import UserRead
from media_manager.auth.users import current_active_user, current_superuser
from media_manager.config import LibraryItem, AllEncompassingConfig
from media_manager.indexer.schemas import PublicIndexerQueryResult, IndexerQueryResultId
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.torrent.schemas import Torrent
from media_manager.movies import log
from media_manager.exceptions import MediaAlreadyExists
from media_manager.movies.schemas import (
    Movie,
    MovieRequest,
    MovieId,
    RichMovieTorrent,
    PublicMovie,
    PublicMovieFile,
    CreateMovieRequest,
    MovieRequestId,
    RichMovieRequest,
)
from media_manager.movies.dependencies import (
    movie_service_dep,
)
from media_manager.metadataProvider.dependencies import metadata_provider_dep
from media_manager.movies.schemas import MovieRequestBase

router = APIRouter()


# --------------------------------
# CREATE AND DELETE MOVIES
# --------------------------------


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_201_CREATED: {
            "model": Movie,
            "description": "Successfully created movie",
        },
        status.HTTP_409_CONFLICT: {"model": str, "description": "Movie already exists"},
    },
)
def add_a_movie(
    movie_service: movie_service_dep,
    metadata_provider: metadata_provider_dep,
    movie_id: int,
):
    try:
        movie = movie_service.add_movie(
            external_id=movie_id,
            metadata_provider=metadata_provider,
        )
    except MediaAlreadyExists as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT, content={"message": str(e)}
        )
    return movie


# --------------------------------
# GET MOVIES
# --------------------------------


@router.get(
    "",
    dependencies=[Depends(current_active_user)],
    response_model=list[PublicMovie],
)
def get_all_movies(movie_service: movie_service_dep):
    return movie_service.get_all_movies()


@router.get(
    "/libraries",
    dependencies=[Depends(current_active_user)],
    response_model=list[LibraryItem],
)
def get_available_libraries():
    return AllEncompassingConfig().misc.movie_libraries


@router.get(
    "/search",
    dependencies=[Depends(current_active_user)],
    response_model=list[MetaDataProviderSearchResult],
)
def search_for_movie(
    query: str,
    movie_service: movie_service_dep,
    metadata_provider: metadata_provider_dep,
):
    return movie_service.search_for_movie(
        query=query, metadata_provider=metadata_provider
    )


@router.get(
    "/recommended",
    dependencies=[Depends(current_active_user)],
    response_model=list[MetaDataProviderSearchResult],
)
def get_popular_movies(
    movie_service: movie_service_dep,
    metadata_provider: metadata_provider_dep,
):
    return movie_service.get_popular_movies(metadata_provider=metadata_provider)


@router.get(
    "/torrents",
    dependencies=[Depends(current_active_user)],
    response_model=list[RichMovieTorrent],
)
def get_all_movies_with_torrents(movie_service: movie_service_dep):
    return movie_service.get_all_movies_with_torrents()


# --------------------------------
# MOVIE REQUESTS
# --------------------------------


@router.post(
    "/requests",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieRequest,
)
def create_movie_request(
    movie_service: movie_service_dep,
    movie_request: CreateMovieRequest,
    user: Annotated[UserRead, Depends(current_active_user)],
):
    log.info(
        f"User {user.email} is creating a movie request for {movie_request.movie_id}"
    )
    movie_request = MovieRequest.model_validate(movie_request)
    movie_request.requested_by = user
    log.info("SERVASasdasd")
    if user.is_superuser:
        movie_request.authorized = True
        movie_request.authorized_by = user

    return movie_service.add_movie_request(movie_request=movie_request)


@router.get(
    "/requests",
    dependencies=[Depends(current_active_user)],
    response_model=list[RichMovieRequest],
)
def get_all_movie_requests(movie_service: movie_service_dep):
    return movie_service.get_all_movie_requests()


@router.put(
    "/requests/{movie_request_id}",
    response_model=MovieRequest,
)
def update_movie_request(
    movie_service: movie_service_dep,
    movie_request_id: MovieRequestId,
    update_movie_request: MovieRequestBase,
    user: Annotated[UserRead, Depends(current_active_user)],
):
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
):
    """
    updates the request flag to true
    """
    movie_request = movie_service.get_movie_request_by_id(
        movie_request_id=movie_request_id
    )
    movie_request.authorized = authorized_status
    if authorized_status:
        movie_request.authorized_by = user
    else:
        movie_request.authorized_by = None
    return movie_service.update_movie_request(movie_request=movie_request)


@router.delete(
    "/requests/{movie_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_movie_request(
    movie_service: movie_service_dep, movie_request_id: MovieRequestId
):
    movie_service.delete_movie_request(movie_request_id=movie_request_id)


# --------------------------------
# TORRENTS
# --------------------------------


@router.get(
    "/{movie_id}",
    dependencies=[Depends(current_active_user)],
    response_model=PublicMovie,
)
def get_movie_by_id(movie_service: movie_service_dep, movie_id: MovieId):
    return movie_service.get_public_movie_by_id(movie_id=movie_id)


@router.get(
    "/{movie_id}/torrents",
    dependencies=[Depends(current_active_user)],
    response_model=list[PublicIndexerQueryResult],
)
def get_all_available_torrents_for_a_movie(
    movie_service: movie_service_dep,
    movie_id: MovieId,
    search_query_override: str | None = None,
):
    return movie_service.get_all_available_torrents_for_a_movie(
        movie_id=movie_id, search_query_override=search_query_override
    )


@router.post(
    "/{movie_id}/torrents",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
    response_model=Torrent,
)
def download_torrent_for_movie(
    movie_service: movie_service_dep,
    movie_id: MovieId,
    public_indexer_result_id: IndexerQueryResultId,
    override_file_path_suffix: str = "",
):
    return movie_service.download_torrent(
        public_indexer_result_id=public_indexer_result_id,
        movie_id=movie_id,
        override_movie_file_path_suffix=override_file_path_suffix,
    )


@router.get(
    "/{movie_id}/files",
    dependencies=[Depends(current_active_user)],
    response_model=list[PublicMovieFile],
)
def get_movie_files_by_movie_id(movie_service: movie_service_dep, movie_id: MovieId):
    return movie_service.get_public_movie_files_by_movie_id(movie_id=movie_id)


@router.post(
    "/{movie_id}/library",
    dependencies=[Depends(current_superuser)],
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_library(
    movie_id: MovieId,
    movie_service: movie_service_dep,
    library: str,
) -> None:
    """
    Sets the library of a movie.
    """
    movie_service.set_movie_library(movie_id=movie_id, library=library)
    return
