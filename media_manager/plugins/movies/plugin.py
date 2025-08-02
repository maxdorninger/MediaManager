from typing import Type, List
from fastapi import APIRouter

from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig
from media_manager.plugins.movies.models import Movie, MovieFile, MovieRequest
from media_manager.plugins.movies.service import MoviePluginService
from media_manager.plugins.movies.repository import MoviePluginRepository
from media_manager.plugins.movies.router import get_movie_router


class MoviePlugin(BaseMediaPlugin):
    """
    Movies plugin for MediaManager
    """
    
    @property
    def plugin_info(self) -> MediaPluginInfo:
        return MediaPluginInfo(
            name="movies",
            display_name="Movies",
            version="1.0.0",
            description="Manage movies with automatic downloading and organization",
            media_type="movie",
            supported_extensions=[".mkv", ".mp4", ".avi", ".m4v"],
            metadata_providers=["tmdb"]
        )
    
    @property
    def media_model_class(self) -> Type[Movie]:
        return Movie
    
    @property
    def router(self) -> APIRouter:
        return get_movie_router()
    
    def get_service(self, **dependencies) -> BaseMediaService:
        """Get the Movie service instance"""
        session = dependencies.get('session')
        if not session:
            raise ValueError("Session dependency is required")
        
        repository = self.get_repository(session)
        self._service = MoviePluginService(repository, **dependencies)
        return self._service
    
    def get_repository(self, session, **kwargs) -> BaseMediaRepository:
        """Get the Movie repository instance"""
        self._repository = MoviePluginRepository(session)
        return self._repository
    
    def get_database_models(self) -> List[Type]:
        """Get all database models for Movie plugin"""
        return [Movie, MovieFile, MovieRequest]
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        """Validate Movie plugin configuration"""
        # Check that at least one library path is configured
        if not config.libraries:
            return False
        
        # Validate library paths exist or can be created
        for library in config.libraries:
            if library.enabled and not library.path:
                return False
        
        return True
    
    def on_startup(self) -> None:
        """Called when the Movie plugin is loaded"""
        print(f"Movie Plugin v{self.plugin_info.version} started")
    
    def on_shutdown(self) -> None:
        """Called when the application shuts down"""
        print("Movie Plugin shutting down")