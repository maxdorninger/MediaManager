from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from media_manager.database import get_session
from media_manager.plugins.tv.service import TvPluginService
from media_manager.plugins.tv.repository import TvPluginRepository
from media_manager.tv.dependencies import get_tv_service
from media_manager.tv import router as tv_router


def get_tv_plugin_service(session: Session = Depends(get_session)) -> TvPluginService:
    """
    Dependency to get TV plugin service
    """
    repository = TvPluginRepository(session)
    # Get the existing dependencies that TvService needs
    tv_service_deps = get_tv_service(session)
    
    return TvPluginService(
        repository=repository,
        torrent_service=tv_service_deps.torrent_service,
        indexer_service=tv_service_deps.indexer_service,
        notification_service=tv_service_deps.notification_service,
        metadata_provider=tv_service_deps.metadata_provider,
        config=tv_service_deps.config
    )


# For now, we'll use the existing TV router to maintain API compatibility
# In the future, this could be replaced with plugin-specific routes
def get_tv_router() -> APIRouter:
    """
    Get the TV plugin router
    """
    return tv_router.router