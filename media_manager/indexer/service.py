import logging

from media_manager.config import MediaManagerConfig
from media_manager.indexer.indexers.generic import GenericIndexer
from media_manager.indexer.indexers.jackett import Jackett
from media_manager.indexer.indexers.prowlarr import Prowlarr
from media_manager.indexer.repository import IndexerRepository
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.movies.schemas import Movie
from media_manager.torrent.utils import remove_special_chars_and_parentheses
from media_manager.tv.schemas import Show

log = logging.getLogger(__name__)


class IndexerService:
    def __init__(self, indexer_repository: IndexerRepository) -> None:
        config = MediaManagerConfig()
        self.repository = indexer_repository
        self.indexers: list[GenericIndexer] = []

        if config.indexers.prowlarr.enabled:
            self.indexers.append(Prowlarr())
        if config.indexers.jackett.enabled:
            self.indexers.append(Jackett())

    def get_result(self, result_id: IndexerQueryResultId) -> IndexerQueryResult:
        return self.repository.get_result(result_id=result_id)

    def search(self, query: str, is_tv: bool) -> list[IndexerQueryResult]:
        """
        Search for results using the indexers based on a query.

        :param is_tv: Whether the search is for TV shows or movies.
        :param query: The search query, is used as a fallback in case indexers don't support e.g. TMDB ID based search.
        :return: A list of search results.
        """
        log.debug(f"Searching for: {query}")
        results = []

        for indexer in self.indexers:
            try:
                indexer_results = indexer.search(query, is_tv=is_tv)
                results.extend(indexer_results)
                log.debug(
                    f"Indexer {indexer.__class__.__name__} returned {len(indexer_results)} results for query: {query}"
                )
            except Exception:
                log.exception(
                    f"Indexer {indexer.__class__.__name__} failed for query '{query}'"
                )

        for result in results:
            self.repository.save_result(result=result)

        return results

    def search_movie(self, movie: Movie) -> list[IndexerQueryResult]:
        query = f"{movie.name} {movie.year}"
        query = remove_special_chars_and_parentheses(query)

        results = []
        for indexer in self.indexers:
            try:
                indexer_results = indexer.search_movie(query=query, movie=movie)
                if indexer_results:
                    results.extend(indexer_results)
            except Exception:
                log.exception(
                    f"Indexer {indexer.__class__.__name__} failed for movie search '{query}'"
                )

        for result in results:
            self.repository.save_result(result=result)

        return results

    def search_season(self, show: Show, season_number: int) -> list[IndexerQueryResult]:
        query = f"{show.name} {show.year} S{season_number:02d}"
        query = remove_special_chars_and_parentheses(query)

        results = []
        for indexer in self.indexers:
            try:
                indexer_results = indexer.search_season(
                    query=query, show=show, season_number=season_number
                )
                if indexer_results:
                    results.extend(indexer_results)
            except Exception:
                log.exception(
                    f"Indexer {indexer.__class__.__name__} failed for season search '{query}'"
                )

        for result in results:
            self.repository.save_result(result=result)

        return results
