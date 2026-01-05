import logging
from dataclasses import dataclass

from requests import Session

from media_manager.config import MediaManagerConfig
from media_manager.indexer.indexers.generic import GenericIndexer
from media_manager.indexer.indexers.torznab_mixin import TorznabMixin
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.movies.schemas import Movie
from media_manager.tv.schemas import Show

log = logging.getLogger(__name__)


@dataclass
class IndexerInfo:
    id: int
    name: str

    supports_tv_search: bool
    supports_tv_search_tmdb: bool
    supports_tv_search_imdb: bool
    supports_tv_search_tvdb: bool
    supports_tv_search_season: bool

    supports_movie_search: bool
    supports_movie_search_tmdb: bool
    supports_movie_search_imdb: bool
    supports_movie_search_tvdb: bool


class Prowlarr(GenericIndexer, TorznabMixin):
    def __init__(self):
        """
        A subclass of GenericIndexer for interacting with the Prowlarr API.
        """
        super().__init__(name="prowlarr")
        self.config = MediaManagerConfig().indexers.prowlarr

    def _call_prowlarr_api(self, path: str, parameters: dict = None):
        url = f"{self.config.url}/api/v1{path}"
        headers = {"X-Api-Key": self.config.api_key}
        with Session() as session:
            return session.get(
                url=url,
                params=parameters,
                timeout=self.config.timeout_seconds,
                headers=headers,
            )

    def _newznab_search(
        self, indexer: IndexerInfo, parameters: dict = None
    ) -> list[IndexerQueryResult]:
        if parameters is None:
            parameters = {}

        parameters["limit"] = 10000
        results = self._call_prowlarr_api(
            path=f"/indexer/{indexer.id}/newznab", parameters=parameters
        )
        results = self.process_search_result(xml=results.content)
        log.info(
            f"Indexer {indexer.name} returned {len(results)} results for search: {parameters}"
        )
        return results

    def _get_indexers(self) -> list[IndexerInfo]:
        indexers = self._call_prowlarr_api(path="/indexer")
        indexers = indexers.json()
        indexer_info_list: list[IndexerInfo] = []
        for indexer in indexers:
            supports_tv_search = False
            supports_movie_search = False
            tv_search_params = []
            movie_search_params = []

            if not indexer["capabilities"].get("tvSearchParams"):
                supports_tv_search = False
            else:
                supports_tv_search = True
                tv_search_params = indexer["capabilities"]["tvSearchParams"]

            if not indexer["capabilities"].get("movieSearchParams"):
                supports_movie_search = False
            else:
                supports_movie_search = True
                movie_search_params = indexer["capabilities"]["movieSearchParams"]

            indexer_info = IndexerInfo(
                id=indexer["id"],
                name=indexer.get("name", "unknown"),
                supports_tv_search=supports_tv_search,
                supports_tv_search_tmdb="tmdbId" in tv_search_params,
                supports_tv_search_imdb="imdbId" in tv_search_params,
                supports_tv_search_tvdb="tvdbId" in tv_search_params,
                supports_tv_search_season="season" in tv_search_params,
                supports_movie_search=supports_movie_search,
                supports_movie_search_tmdb="tmdbId" in movie_search_params,
                supports_movie_search_imdb="imdbId" in movie_search_params,
                supports_movie_search_tvdb="tvdbId" in movie_search_params,
            )
            indexer_info_list.append(indexer_info)
        return indexer_info_list

    def _get_tv_indexers(self) -> list[IndexerInfo]:
        return [x for x in self._get_indexers() if x.supports_tv_search]

    def _get_movie_indexers(self) -> list[IndexerInfo]:
        return [x for x in self._get_indexers() if x.supports_movie_search]

    def search(self, query: str, is_tv: bool) -> list[IndexerQueryResult]:
        log.info(f"Searching for: {query}")
        params = {
            "q": query,
            "t": "tvsearch" if is_tv else "movie",
        }
        raw_results = []
        indexers = self._get_tv_indexers() if is_tv else self._get_movie_indexers()

        for indexer in indexers:
            raw_results.extend(self._newznab_search(parameters=params, indexer=indexer))

        return raw_results

    def search_season(
        self, query: str, show: Show, season_number: int
    ) -> list[IndexerQueryResult]:
        indexers = self._get_tv_indexers()

        raw_results = []

        for indexer in indexers:
            log.debug("Preparing search for indexer: " + indexer.name)
            search_params = {
                "cat": "5000",
                "q": query,
                "t": "tvsearch",
            }

            if indexer.supports_tv_search_tmdb and show.metadata_provider == "tmdb":
                search_params["tmdbid"] = show.external_id
            if indexer.supports_tv_search_tvdb and show.metadata_provider == "tvdb":
                search_params["tvdbid"] = show.external_id
            if indexer.supports_tv_search_imdb:
                search_params["imdbid"] = show.imdb_id
            if indexer.supports_tv_search_season:
                search_params["season"] = season_number

            raw_results.extend(
                self._newznab_search(parameters=search_params, indexer=indexer)
            )

        return raw_results

    def search_movie(self, query: str, movie: Movie) -> list[IndexerQueryResult]:
        indexers = self._get_movie_indexers()

        raw_results = []

        for indexer in indexers:
            log.debug("Preparing search for indexer: " + indexer.name)

            search_params = {
                "cat": "2000",
                "q": query,
                "t": "movie",
            }

            if indexer.supports_movie_search_tmdb and movie.metadata_provider == "tmdb":
                search_params["tmdbid"] = movie.external_id
            if indexer.supports_movie_search_tvdb and movie.metadata_provider == "tvdb":
                search_params["tvdbid"] = movie.external_id
            if indexer.supports_movie_search_imdb:
                search_params["imdbid"] = movie.imdb_id

            raw_results.extend(
                self._newznab_search(parameters=search_params, indexer=indexer)
            )

        return raw_results
