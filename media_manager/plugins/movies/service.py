from typing import List, Optional, Any
from uuid import UUID

from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.schemas import MediaPluginInfo
from media_manager.plugins.movies.repository import MoviePluginRepository
from media_manager.movies.service import MovieService
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.indexer.schemas import IndexerQueryResult


class MoviePluginService(BaseMediaService):
    """
    Movie Plugin service that wraps the existing MovieService
    """
    
    def __init__(self, repository: MoviePluginRepository, **dependencies):
        super().__init__(repository)
        self._movie_service = MovieService(
            repository=repository._movie_repo,
            **dependencies
        )
    
    def search_metadata(self, query: str, **kwargs) -> List[MetaDataProviderSearchResult]:
        """Search for movies in metadata providers"""
        return self._movie_service.search_movies(query)
    
    def create_from_metadata(self, metadata_result: MetaDataProviderSearchResult, **kwargs) -> Any:
        """Create movie from metadata provider result"""
        return self._movie_service.create_movie_from_search_result(
            metadata_result, 
            **kwargs
        )
    
    def update_metadata(self, media_id: UUID) -> Optional[Any]:
        """Update metadata for existing movie"""
        return self._movie_service.update_movie_metadata(media_id)
    
    def search_torrents(self, media_id: UUID, **kwargs) -> List[IndexerQueryResult]:
        """Search for torrents for movie"""
        return self._movie_service.search_movie_torrents(media_id)
    
    def create_request(self, media_id: UUID, **kwargs) -> Any:
        """Create a movie download request"""
        return self._movie_service.create_movie_request(
            movie_id=media_id,
            **kwargs
        )
    
    def auto_download_approved_requests(self) -> None:
        """Automatically download approved movie requests"""
        # Use the existing function
        from media_manager.movies.service import auto_download_all_approved_movie_requests
        auto_download_all_approved_movie_requests()
    
    def import_downloaded_files(self) -> None:
        """Import downloaded movie files from torrent directory"""
        # Use the existing function
        from media_manager.movies.service import import_all_movie_torrents
        import_all_movie_torrents()
    
    def get_plugin_info(self) -> MediaPluginInfo:
        """Get information about this plugin"""
        return MediaPluginInfo(
            name="movies",
            display_name="Movies",
            version="1.0.0",
            description="Manage movies with automatic downloading and organization",
            media_type="movie",
            supported_extensions=[".mkv", ".mp4", ".avi", ".m4v"],
            metadata_providers=["tmdb"]
        )
    
    # Movie-specific methods that delegate to the wrapped service
    def get_movie_by_id(self, movie_id: UUID):
        return self._movie_service.get_movie_by_id(movie_id)
    
    def get_movies(self, limit: int = 100, offset: int = 0):
        return self._movie_service.get_movies(limit, offset)
    
    def get_movie_requests(self, **kwargs):
        return self._movie_service.get_movie_requests(**kwargs)
    
    def authorize_movie_request(self, request_id: UUID, user_id: UUID):
        return self._movie_service.authorize_movie_request(request_id, user_id)