from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from media_manager.database import get_session
from media_manager.plugins.movies.service import MoviePluginService
from media_manager.plugins.movies.repository import MoviePluginRepository
from media_manager.movies.dependencies import get_movie_service
from media_manager.movies import router as movie_router


def get_movie_plugin_service(session: Session = Depends(get_session)) -> MoviePluginService:
    """
    Dependency to get Movie plugin service
    """
    repository = MoviePluginRepository(session)
    # Get the existing dependencies that MovieService needs
    movie_service_deps = get_movie_service(session)
    
    return MoviePluginService(
        repository=repository,
        torrent_service=movie_service_deps.torrent_service,
        indexer_service=movie_service_deps.indexer_service,
        notification_service=movie_service_deps.notification_service,
        metadata_provider=movie_service_deps.metadata_provider,
        config=movie_service_deps.config
    )


# For now, we'll use the existing Movie router to maintain API compatibility
# In the future, this could be replaced with plugin-specific routes
def get_movie_router() -> APIRouter:
    """
    Get the Movie plugin router
    """
    return movie_router.router