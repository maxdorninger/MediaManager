import concurrent
import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from requests.adapters import HTTPAdapter

from media_manager.indexer.indexers.generic import GenericIndexer
from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.indexer.utils import follow_redirects_to_final_torrent_url

log = logging.getLogger(__name__)


class Prowlarr(GenericIndexer):
    def __init__(self, **kwargs):
        """
        A subclass of GenericIndexer for interacting with the Prowlarr API.

        :param api_key: The API key for authenticating requests to Prowlarr.
        :param kwargs: Additional keyword arguments to pass to the superclass constructor.
        """
        super().__init__(name="prowlarr")
        config = AllEncompassingConfig().indexers.prowlarr
        self.api_key = config.api_key
        self.url = config.url
        self.reject_torrents_on_url_error = config.reject_torrents_on_url_error
        log.debug("Registering Prowlarr as Indexer")

    def search(self, query: str, is_tv: bool) -> list[IndexerQueryResult]:
        log.debug("Searching for " + query)
        url = self.url + "/api/v1/search"

        params = {
            "query": query,
            "apikey": self.api_key,
            "categories": "5000" if is_tv else "2000",  # TV: 5000, Movies: 2000
            "limit": 10000,
        }
        with requests.Session() as session:
            adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            response = session.get(url, params=params)
            log.debug(f"Prowlarr response time for query '{query}': {response.elapsed}")

            if response.status_code != 200:
                log.error(f"Prowlarr Error: {response.status_code}")
                return []

            futures = []
            result_list: list[IndexerQueryResult] = []

            with ThreadPoolExecutor() as executor:
                for item in response.json():
                    future = executor.submit(self.process_result, item, session)
                    futures.append(future)

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is not None:
                        result_list.append(result)

            return result_list

    def process_result(
        self, result, session: requests.Session
    ) -> IndexerQueryResult | None:
        if result["protocol"] == "torrent":
            initial_url = None
            if "downloadUrl" in result:
                log.info(f"Using download URL: {result['downloadUrl']}")
                initial_url = result["downloadUrl"]
            elif "magnetUrl" in result:
                log.info(
                    f"Using magnet URL as fallback for download URL: {result['magnetUrl']}"
                )
                initial_url = result["magnetUrl"]
            elif "guid" in result:
                log.warning(
                    f"Using guid as fallback for download URL: {result['guid']}"
                )
                initial_url = result["guid"]
            else:
                log.error(f"No valid download URL found for result: {result}")
                return None

            if not initial_url.startswith("magnet:"):
                try:
                    final_download_url = follow_redirects_to_final_torrent_url(
                        initial_url=initial_url,
                        session=session,
                    )
                except RuntimeError as e:
                    log.debug(
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
                seeders=result["seeders"],
                flags=result["indexerFlags"],
                size=result["size"],
                usenet=False,
                age=0,  # Torrent results do not need age information
                indexer=result["indexer"] if "indexer" in result else None,
            )
        else:
            return IndexerQueryResult(
                download_url=result["downloadUrl"],
                title=result["sortTitle"],
                seeders=0,  # Usenet results do not have seeders
                flags=result["indexerFlags"],
                size=result["size"],
                usenet=True,
                age=int(result["ageMinutes"]) * 60,
                indexer=result["indexer"] if "indexer" in result else None,
            )
