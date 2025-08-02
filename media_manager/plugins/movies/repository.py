from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.movies.repository import MovieRepository
from media_manager.plugins.movies.models import Movie, MovieRequest


class MoviePluginRepository(BaseMediaRepository[Movie]):
    """
    Movie Plugin repository that wraps the existing MovieRepository
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Movie)
        self._movie_repo = MovieRepository(session)
    
    def get_downloadable_requests(self) -> List[MovieRequest]:
        """Get movie requests that are ready for download"""
        return self._movie_repo.get_downloadable_movie_requests()
    
    def get_files_by_media_id(self, media_id: UUID) -> List:
        """Get movie files for a specific movie"""
        return self._movie_repo.get_movie_files_by_movie_id(media_id)
    
    # Delegate all existing movie-specific methods to the wrapped repository
    def get_movie_by_id(self, movie_id: UUID) -> Optional[Movie]:
        return self._movie_repo.get_movie_by_id(movie_id)
    
    def get_movies(self, limit: int = 100, offset: int = 0) -> List[Movie]:
        return self._movie_repo.get_movies(limit, offset)
    
    def create_movie(self, **kwargs) -> Movie:
        return self._movie_repo.create_movie(**kwargs)
    
    def create_movie_request(self, **kwargs) -> MovieRequest:
        return self._movie_repo.create_movie_request(**kwargs)
    
    def get_movie_requests(self, **kwargs) -> List[MovieRequest]:
        return self._movie_repo.get_movie_requests(**kwargs)
    
    def update_movie_request(self, request_id: UUID, **kwargs) -> Optional[MovieRequest]:
        return self._movie_repo.update_movie_request(request_id, **kwargs)