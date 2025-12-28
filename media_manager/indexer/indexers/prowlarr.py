import concurrent
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass

from requests import Session
import prowlarr

from media_manager.indexer.indexers.generic import GenericIndexer
from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.indexer.utils import follow_redirects_to_final_torrent_url
from media_manager.movies.schemas import Movie
from media_manager.tv.schemas import Show

log = logging.getLogger(__name__)


@dataclass
class IndexerInfo:
    id: int
    name: str

    supports_tv_search_tmdb: bool
    supports_tv_search_imdb: bool
    supports_tv_search_tvdb: bool
    supports_tv_search_season: bool

    supports_movie_search_tmdb: bool
    supports_movie_search_imdb: bool
    supports_movie_search_tvdb: bool


class Prowlarr(GenericIndexer):
    def __init__(self, **kwargs):
        """
        A subclass of GenericIndexer for interacting with the Prowlarr API.

        :param api_key: The API key for authenticating requests to Prowlarr.
        :param kwargs: Additional keyword arguments to pass to the superclass constructor.
        """
        super().__init__(name="prowlarr")
        config = AllEncompassingConfig().indexers.prowlarr
        configuration = prowlarr.Configuration(host=config.url, retries=3)
        configuration.api_key["X-Api-Key"] = config.api_key
        self.config = configuration
        self.reject_torrents_on_url_error = config.reject_torrents_on_url_error
        self.timeout_seconds = config.timeout_seconds
        self.follow_redirects = config.follow_redirects

    @contextmanager
    def __get_api(self):
        with prowlarr.ApiClient(self.config) as api_instance:
            yield prowlarr.IndexerApi(api_instance)

    def __get_indexers(self) -> list[IndexerInfo]:
        with self.__get_api() as client:
            api = prowlarr.IndexerApi(client)
            indexers = api.list_indexer()
            indexer_info_list: list[IndexerInfo] = []
            for indexer in indexers:
                tv_search_params = (
                    indexer.capabilities.tv_search_params
                    if indexer.capabilities.tv_search_params
                    else []
                )
                movie_search_params = (
                    indexer.capabilities.movie_search_params
                    if indexer.capabilities.movie_search_params
                    else []
                )

                indexer_info = IndexerInfo(
                    id=indexer.id,
                    name=indexer.name,
                    supports_tv_search_tmdb="tmdbId" in tv_search_params,
                    supports_tv_search_imdb="imdbId" in tv_search_params,
                    supports_tv_search_tvdb="tvdbId" in tv_search_params,
                    supports_tv_search_season="season" in tv_search_params,
                    supports_movie_search_tmdb="tmdbId" in movie_search_params,
                    supports_movie_search_imdb="imdbId" in movie_search_params,
                    supports_movie_search_tvdb="tvdbId" in movie_search_params,
                )
                indexer_info_list.append(indexer_info)
            return indexer_info_list

    def search(self, query: str, is_tv: bool) -> list[IndexerQueryResult]:
        log.info(f"Searching for: {query}")
        processed_results: list[IndexerQueryResult] = []
        raw_results = None
        with self.__get_api() as api:
            search_api = prowlarr.SearchApi(api.api_client)

            try:
                raw_results = search_api.list_search(
                    query=query, categories=[5000] if is_tv else [2000], limit=10000
                )
            except Exception as e:
                log.error(f"Prowlarr search error: {e}")
                raise RuntimeError(f"Prowlarr search error: {e}") from e

        for result in raw_results:
            try:
                processed_result = self.__process_result(result=result)
                if processed_result:
                    processed_results.append(processed_result)
            except Exception as e:
                log.error(f"Failed to process result {result}: {e}")

        return processed_results

    def __process_result(self, result) -> IndexerQueryResult | None:
        # process usenet search result
        if result["protocol"] != "torrent":
            return IndexerQueryResult(
                download_url=result["downloadUrl"],
                title=result["sortTitle"],
                seeders=0,  # Usenet results do not have seeders
                flags=result["indexerFlags"] if "indexerFlags" in result else [],
                size=result["size"],
                usenet=True,
                age=int(result["ageMinutes"]) * 60,
                indexer=result["indexer"] if "indexer" in result else None,
            )

        # process torrent search result
        initial_url = None
        if "downloadUrl" in result:
            initial_url = result["downloadUrl"]
        elif "magnetUrl" in result:
            initial_url = result["magnetUrl"]
        elif "guid" in result:
            initial_url = result["guid"]
        else:
            log.debug(f"No valid download URL found for result: {result}")
            raise RuntimeError("No valid download URL found in torrent search result")

        if not initial_url.startswith("magnet:") and self.follow_redirects:
            try:
                final_download_url = follow_redirects_to_final_torrent_url(
                    initial_url=initial_url,
                    session=Session(),
                    timeout=self.timeout_seconds,
                )
            except RuntimeError as e:
                log.warning(
                    f"Failed to follow redirects for {initial_url}, falling back to the initial url as download url, error: {e}"
                )
                if self.reject_torrents_on_url_error:
                    return None
                else:
                    final_download_url = initial_url
        else:
            final_download_url = initial_url

        return IndexerQueryResult(
            download_url=final_download_url,
            title=result["sortTitle"],
            seeders=result["seeders"] if "seeders" in result else 0,
            flags=result["indexerFlags"] if "indexerFlags" in result else [],
            size=result["size"],
            usenet=False,
            age=0,  # Torrent results do not need age information
            indexer=result["indexer"] if "indexer" in result else None,
        )

    def __process_results(self, results: list) -> list[IndexerQueryResult]:
        processed_results: list[IndexerQueryResult] = []
        for result in results:
            try:
                processed_result = self.__process_result(result=result)
                if processed_result:
                    processed_results.append(processed_result)
            except Exception as e:
                log.error(f"Failed to process result {result}: {e}")
        return processed_results

    def __get_newznab_api(self, searches: list) -> list:
        results = []
        with prowlarr.NewznabApi(self.__get_api) as api:
            futures = []
            with ThreadPoolExecutor() as executor:
                for search in searches:
                    future = executor.submit(api.get_indexer_newznab, **search)
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result is not None:
                            results.extend(result)
                    except Exception as e:
                        log.error(f"Querying one indexer failed because: {e}")
        return results

    def search_season(
        self, query: str, show: Show, season_number: int
    ) -> list[IndexerQueryResult]:
        indexers = self.__get_indexers()

        searches = []
        for indexer in indexers:
            search_params = {
                "id": indexer.id,
                "cat": "5000",
                "limit": 10000,
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

            searches.append(search_params)

        raw_results = self.__get_newznab_api(searches=searches)

        search_results = self.__process_results(results=raw_results)

        return search_results

    def search_movie(self, query: str, movie: Movie) -> list[IndexerQueryResult]:
        indexers = self.__get_indexers()

        searches = []
        for indexer in indexers:
            search_params = {
                "id": indexer.id,
                "cat": "2000",
                "limit": 10000,
                "q": query,
                "t": "movie",
            }

            if indexer.supports_movie_search_tmdb and movie.metadata_provider == "tmdb":
                search_params["tmdbid"] = movie.external_id
            if indexer.supports_movie_search_tvdb and movie.metadata_provider == "tvdb":
                search_params["tvdbid"] = movie.external_id
            if indexer.supports_movie_search_imdb:
                search_params["imdbid"] = movie.imdb_id

            searches.append(search_params)

        raw_results = self.__get_newznab_api(searches=searches)

        search_results = self.__process_results(results=raw_results)

        return search_results
