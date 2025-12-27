from abc import abstractmethod, ABC

from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.movies.schemas import Movie
from media_manager.tv.schemas import Show


class GenericIndexer(ABC):
    name: str

    def __init__(self, name: str = None):
        if name:
            self.name = name
        else:
            raise ValueError("indexer name must not be None")

    @abstractmethod
    def search(self, query: str, is_tv: bool) -> list[IndexerQueryResult]:
        """
        Sends a search request to the Indexer and returns the results.

        :param query: A string representing the search query.
        :param is_tv: A boolean indicating whether the search is for TV shows (True) or movies (False).
        :return: A list of IndexerQueryResult objects representing the search results.
        """
        raise NotImplementedError()

    @abstractmethod
    def search_season(
        self, query: str, show: Show, season_number: int
    ) -> list[IndexerQueryResult]:
        """
        Sends a search request to the Indexer for a specific season and returns the results.

        :param query: A string representing the search query, used as a fallback for indexers that don't support TMDB/IMDB ID-based search.
        :param show: The show to search for.
        :param season_number: The season number to search for.
        :return: A list of IndexerQueryResult objects representing the search results.
        """
        raise NotImplementedError()

    @abstractmethod
    def search_movie(self, query: str, movie: Movie) -> list[IndexerQueryResult]:
        """
        Sends a search request to the Indexer for a specific movie and returns the results.

        :param movie: The movie to search for.
        :param query: A string representing the search query, used as a fallback for indexers that don't support TMDB/IMDB ID-based search.
        :return: A list of IndexerQueryResult objects representing the search results.
        """
        raise NotImplementedError()
