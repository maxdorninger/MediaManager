from typing import Type, List
from fastapi import APIRouter

from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig
from media_manager.plugins.tv.models import Show, Season, Episode, SeasonFile, SeasonRequest
from media_manager.plugins.tv.service import TvPluginService
from media_manager.plugins.tv.repository import TvPluginRepository
from media_manager.plugins.tv.router import get_tv_router


class TvPlugin(BaseMediaPlugin):
    """
    TV Shows plugin for MediaManager
    """
    
    @property
    def plugin_info(self) -> MediaPluginInfo:
        return MediaPluginInfo(
            name="tv",
            display_name="TV Shows",
            version="1.0.0",
            description="Manage TV shows with automatic season and episode tracking",
            media_type="tv",
            supported_extensions=[".mkv", ".mp4", ".avi", ".m4v", ".ts"],
            metadata_providers=["tvdb", "tmdb"]
        )
    
    @property
    def media_model_class(self) -> Type[Show]:
        return Show
    
    @property
    def router(self) -> APIRouter:
        return get_tv_router()
    
    def get_service(self, **dependencies) -> BaseMediaService:
        """Get the TV service instance"""
        session = dependencies.get('session')
        if not session:
            raise ValueError("Session dependency is required")
        
        repository = self.get_repository(session)
        self._service = TvPluginService(repository, **dependencies)
        return self._service
    
    def get_repository(self, session, **kwargs) -> BaseMediaRepository:
        """Get the TV repository instance"""
        self._repository = TvPluginRepository(session)
        return self._repository
    
    def get_database_models(self) -> List[Type]:
        """Get all database models for TV plugin"""
        return [Show, Season, Episode, SeasonFile, SeasonRequest]
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        """Validate TV plugin configuration"""
        # Check that at least one library path is configured
        if not config.libraries:
            return False
        
        # Validate library paths exist or can be created
        for library in config.libraries:
            if library.enabled and not library.path:
                return False
        
        return True
    
    def on_startup(self) -> None:
        """Called when the TV plugin is loaded"""
        print(f"TV Plugin v{self.plugin_info.version} started")
    
    def on_shutdown(self) -> None:
        """Called when the application shuts down"""
        print("TV Plugin shutting down")