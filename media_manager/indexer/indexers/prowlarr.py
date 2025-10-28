import logging

import requests

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

        response = requests.get(url, params=params)
        if response.status_code == 200:
            result_list: list[IndexerQueryResult] = []
            for result in response.json():
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
                        continue

                    if not initial_url.startswith("magnet:"):
                        try:
                            final_download_url = follow_redirects_to_final_torrent_url(
                                initial_url=initial_url
                            )
                        except RuntimeError as e:
                            log.error(
                                f"Failed to follow redirects for {initial_url}, falling back to the initial url as download url, error: {e}"
                            )
                            final_download_url = initial_url
                    else:
                        final_download_url = initial_url
                    result_list.append(
                        IndexerQueryResult(
                            download_url=final_download_url,
                            title=result["sortTitle"],
                            seeders=result["seeders"],
                            flags=result["indexerFlags"],
                            size=result["size"],
                            usenet=False,
                            age=0,  # Torrent results do not need age information
                            indexer=result["indexer"] if "indexer" in result else None,
                        )
                    )
                else:
                    result_list.append(
                        IndexerQueryResult(
                            download_url=result["downloadUrl"],
                            title=result["sortTitle"],
                            seeders=0,  # Usenet results do not have seeders
                            flags=result["indexerFlags"],
                            size=result["size"],
                            usenet=True,
                            age=int(result["ageMinutes"]) * 60,
                            indexer=result["indexer"] if "indexer" in result else None,
                        )
                    )
                log.debug("torrent result: " + result.__str__())

            return result_list
        else:
            log.error(f"Prowlarr Error: {response.status_code}")
            return []
