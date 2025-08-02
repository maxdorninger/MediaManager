from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.tv.repository import TvRepository
from media_manager.plugins.tv.models import Show, SeasonRequest


class TvPluginRepository(BaseMediaRepository[Show]):
    """
    TV Plugin repository that wraps the existing TvRepository
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Show)
        self._tv_repo = TvRepository(session)
    
    def get_downloadable_requests(self) -> List[SeasonRequest]:
        """Get season requests that are ready for download"""
        return self._tv_repo.get_downloadable_season_requests()
    
    def get_files_by_media_id(self, media_id: UUID) -> List:
        """Get season files for a specific show"""
        return self._tv_repo.get_season_files_by_show_id(media_id)
    
    # Delegate all existing TV-specific methods to the wrapped repository
    def get_show_by_id(self, show_id: UUID) -> Optional[Show]:
        return self._tv_repo.get_show_by_id(show_id)
    
    def get_shows(self, limit: int = 100, offset: int = 0) -> List[Show]:
        return self._tv_repo.get_shows(limit, offset)
    
    def get_season_by_id(self, season_id: UUID):
        return self._tv_repo.get_season_by_id(season_id)
    
    def create_show(self, **kwargs) -> Show:
        return self._tv_repo.create_show(**kwargs)
    
    def create_season_request(self, **kwargs) -> SeasonRequest:
        return self._tv_repo.create_season_request(**kwargs)
    
    def get_season_requests(self, **kwargs) -> List[SeasonRequest]:
        return self._tv_repo.get_season_requests(**kwargs)
    
    def update_season_request(self, request_id: UUID, **kwargs) -> Optional[SeasonRequest]:
        return self._tv_repo.update_season_request(request_id, **kwargs)