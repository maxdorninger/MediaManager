import concurrent
import logging
from concurrent.futures.thread import ThreadPoolExecutor

import requests

from media_manager.config import MediaManagerConfig
from media_manager.indexer.indexers.generic import GenericIndexer
from media_manager.indexer.indexers.torznab_mixin import TorznabMixin
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.movies.schemas import Movie
from media_manager.tv.schemas import Show

log = logging.getLogger(__name__)


class Jackett(GenericIndexer, TorznabMixin):
    def __init__(self):
        """
        A subclass of GenericIndexer for interacting with the Jacket API.

        """
        super().__init__(name="jackett")
        config = MediaManagerConfig().indexers.jackett
        self.api_key = config.api_key
        self.url = config.url
        self.indexers = config.indexers
        self.timeout_seconds = config.timeout_seconds

    def search(self, query: str, is_tv: bool) -> list[IndexerQueryResult]:
        log.debug("Searching for " + query)

        futures = []
        with ThreadPoolExecutor() as executor, requests.Session() as session:
            for indexer in self.indexers:
                future = executor.submit(
                    self.get_torrents_by_indexer, indexer, query, is_tv, session
                )
                futures.append(future)

            responses = []

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        responses.extend(result)
                except Exception as e:
                    log.error(f"search result failed with: {e}")

        return responses

    def get_torrents_by_indexer(
        self, indexer: str, query: str, is_tv: bool, session: requests.Session
    ) -> list[IndexerQueryResult]:
        url = (
            self.url
            + f"/api/v2.0/indexers/{indexer}/results/torznab/api?apikey={self.api_key}&t={'tvsearch' if is_tv else 'movie'}&q={query}"
        )
        response = session.get(url, timeout=self.timeout_seconds)

        if response.status_code != 200:
            log.error(
                f"Jacket error with indexer {indexer}, error: {response.status_code}"
            )
            return []

        results = self.process_search_result(response.content)

        log.info(f"Indexer {indexer} returned {len(results)} results")
        return results

    def search_season(
        self, query: str, show: Show, season_number: int
    ) -> list[IndexerQueryResult]:
        pass

    def search_movie(self, query: str, movie: Movie) -> list[IndexerQueryResult]:
        pass
