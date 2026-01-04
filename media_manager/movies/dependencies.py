from typing import Annotated

from fastapi import Depends, Path

from media_manager.database import DbSessionDependency
from media_manager.movies.repository import MovieRepository
from media_manager.movies.schemas import Movie, MovieId
from media_manager.movies.service import MovieService
from media_manager.exceptions import NotFoundError
from fastapi import HTTPException
from media_manager.indexer.dependencies import indexer_service_dep
from media_manager.torrent.dependencies import torrent_service_dep
from media_manager.notification.dependencies import notification_service_dep


def get_movie_repository(db_session: DbSessionDependency) -> MovieRepository:
    return MovieRepository(db_session)


movie_repository_dep = Annotated[MovieRepository, Depends(get_movie_repository)]


def get_movie_service(
    movie_repository: movie_repository_dep,
    torrent_service: torrent_service_dep,
    indexer_service: indexer_service_dep,
    notification_service: notification_service_dep,
) -> MovieService:
    return MovieService(
        movie_repository=movie_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
        notification_service=notification_service,
    )


movie_service_dep = Annotated[MovieService, Depends(get_movie_service)]


def get_movie_by_id(
    movie_service: movie_service_dep,
    movie_id: MovieId = Path(..., description="The ID of the movie"),
) -> Movie:
    try:
        movie = movie_service.get_movie_by_id(movie_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Movie with ID {movie_id} not found.",
        ) from None
    return movie


movie_dep = Annotated[Movie, Depends(get_movie_by_id)]
