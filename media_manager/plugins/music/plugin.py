from typing import Type, List
from fastapi import APIRouter

from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig
from media_manager.plugins.music.models import Artist, Album, Track, AlbumFile, AlbumRequest
from media_manager.plugins.music.service import MusicPluginService
from media_manager.plugins.music.repository import MusicPluginRepository
from media_manager.plugins.music.router import get_music_router


class MusicPlugin(BaseMediaPlugin):
    """
    Music plugin for MediaManager
    """
    
    @property
    def plugin_info(self) -> MediaPluginInfo:
        return MediaPluginInfo(
            name="music",
            display_name="Music",
            version="1.0.0",
            description="Manage music with automatic album and track organization",
            media_type="music",
            supported_extensions=[".mp3", ".flac", ".m4a", ".ogg", ".wav"],
            metadata_providers=["musicbrainz", "lastfm", "discogs"]
        )
    
    @property
    def media_model_class(self) -> Type[Artist]:
        return Artist
    
    @property
    def router(self) -> APIRouter:
        return get_music_router()
    
    def get_service(self, **dependencies) -> BaseMediaService:
        """Get the Music service instance"""
        session = dependencies.get('session')
        if not session:
            raise ValueError("Session dependency is required")
        
        repository = self.get_repository(session)
        self._service = MusicPluginService(repository, **dependencies)
        return self._service
    
    def get_repository(self, session, **kwargs) -> BaseMediaRepository:
        """Get the Music repository instance"""
        self._repository = MusicPluginRepository(session)
        return self._repository
    
    def get_database_models(self) -> List[Type]:
        """Get all database models for Music plugin"""
        return [Artist, Album, Track, AlbumFile, AlbumRequest]
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        """Validate Music plugin configuration"""
        # Check that at least one library path is configured
        if not config.libraries:
            return False
        
        # Validate library paths exist or can be created
        for library in config.libraries:
            # Handle both dict and object forms of library config
            if isinstance(library, dict):
                enabled = library.get('enabled', True)
                path = library.get('path', '')
            else:
                enabled = getattr(library, 'enabled', True)
                path = getattr(library, 'path', '')
            
            if enabled and not path:
                return False
        
        return True
    
    def on_startup(self) -> None:
        """Called when the Music plugin is loaded"""
        print(f"Music Plugin v{self.plugin_info.version} started")
        print("Note: Music plugin is a demonstration of the plugin system")
        print("Full music metadata provider integration would be implemented here")
    
    def on_shutdown(self) -> None:
        """Called when the application shuts down"""
        print("Music Plugin shutting down")