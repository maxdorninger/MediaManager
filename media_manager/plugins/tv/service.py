from typing import List, Optional, Any
from uuid import UUID

from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.schemas import MediaPluginInfo
from media_manager.plugins.tv.repository import TvPluginRepository
from media_manager.tv.service import TvService
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.indexer.schemas import IndexerQueryResult


class TvPluginService(BaseMediaService):
    """
    TV Plugin service that wraps the existing TvService
    """
    
    def __init__(self, repository: TvPluginRepository, **dependencies):
        super().__init__(repository)
        self._tv_service = TvService(
            repository=repository._tv_repo,
            **dependencies
        )
    
    def search_metadata(self, query: str, **kwargs) -> List[MetaDataProviderSearchResult]:
        """Search for TV shows in metadata providers"""
        return self._tv_service.search_shows(query)
    
    def create_from_metadata(self, metadata_result: MetaDataProviderSearchResult, **kwargs) -> Any:
        """Create show from metadata provider result"""
        return self._tv_service.create_show_from_search_result(
            metadata_result, 
            **kwargs
        )
    
    def update_metadata(self, media_id: UUID) -> Optional[Any]:
        """Update metadata for existing show"""
        return self._tv_service.update_show_metadata(media_id)
    
    def search_torrents(self, media_id: UUID, **kwargs) -> List[IndexerQueryResult]:
        """Search for torrents for show seasons"""
        season_id = kwargs.get('season_id')
        if season_id:
            return self._tv_service.search_season_torrents(season_id)
        return []
    
    def create_request(self, media_id: UUID, **kwargs) -> Any:
        """Create a season download request"""
        return self._tv_service.create_season_request(
            season_id=kwargs.get('season_id', media_id),
            **kwargs
        )
    
    def auto_download_approved_requests(self) -> None:
        """Automatically download approved season requests"""
        # Use the existing function
        from media_manager.tv.service import auto_download_all_approved_season_requests
        auto_download_all_approved_season_requests()
    
    def import_downloaded_files(self) -> None:
        """Import downloaded TV show files from torrent directory"""
        # Use the existing function
        from media_manager.tv.service import import_all_show_torrents
        import_all_show_torrents()
    
    def get_plugin_info(self) -> MediaPluginInfo:
        """Get information about this plugin"""
        return MediaPluginInfo(
            name="tv",
            display_name="TV Shows",
            version="1.0.0",
            description="Manage TV shows with automatic season and episode tracking",
            media_type="tv",
            supported_extensions=[".mkv", ".mp4", ".avi", ".m4v"],
            metadata_providers=["tvdb", "tmdb"]
        )
    
    # TV-specific methods that delegate to the wrapped service
    def get_show_by_id(self, show_id: UUID):
        return self._tv_service.get_show_by_id(show_id)
    
    def get_shows(self, limit: int = 100, offset: int = 0):
        return self._tv_service.get_shows(limit, offset)
    
    def get_season_by_id(self, season_id: UUID):
        return self._tv_service.get_season_by_id(season_id)
    
    def get_season_requests(self, **kwargs):
        return self._tv_service.get_season_requests(**kwargs)
    
    def authorize_season_request(self, request_id: UUID, user_id: UUID):
        return self._tv_service.authorize_season_request(request_id, user_id)