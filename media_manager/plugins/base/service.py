from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.indexer.schemas import IndexerQueryResult

T = TypeVar('T')


class BaseMediaService(ABC):
    """
    Abstract base service for media types
    """
    
    def __init__(self, repository: BaseMediaRepository):
        self.repository = repository
    
    @abstractmethod
    def search_metadata(self, query: str, **kwargs) -> List[MetaDataProviderSearchResult]:
        """Search for media in metadata providers"""
        pass
    
    @abstractmethod
    def create_from_metadata(self, metadata_result: MetaDataProviderSearchResult, **kwargs) -> Any:
        """Create media from metadata provider result"""
        pass
    
    @abstractmethod
    def update_metadata(self, media_id: UUID) -> Optional[Any]:
        """Update metadata for existing media"""
        pass
    
    @abstractmethod
    def search_torrents(self, media_id: UUID, **kwargs) -> List[IndexerQueryResult]:
        """Search for torrents/downloads for this media"""
        pass
    
    @abstractmethod
    def create_request(self, media_id: UUID, **kwargs) -> Any:
        """Create a download request for media"""
        pass
    
    @abstractmethod
    def auto_download_approved_requests(self) -> None:
        """Automatically download approved requests"""
        pass
    
    @abstractmethod
    def import_downloaded_files(self) -> None:
        """Import downloaded files from torrent directory"""
        pass
    
    @abstractmethod
    def get_plugin_info(self) -> MediaPluginInfo:
        """Get information about this plugin"""
        pass
    
    def get_by_id(self, media_id: UUID) -> Optional[Any]:
        """Get media by ID"""
        return self.repository.get_by_id(media_id)
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Get all media with pagination"""
        return self.repository.get_all(limit, offset)
    
    def search_by_name(self, name: str, limit: int = 20) -> List[Any]:
        """Search media by name"""
        return self.repository.search_by_name(name, limit)