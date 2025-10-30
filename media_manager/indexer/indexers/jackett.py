import concurrent
import logging
import xml.etree.ElementTree as ET
from concurrent.futures.thread import ThreadPoolExecutor
from xml.etree.ElementTree import Element

import requests

from media_manager.indexer.indexers.generic import GenericIndexer
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.config import AllEncompassingConfig

log = logging.getLogger(__name__)


class Jackett(GenericIndexer):
    def __init__(self, **kwargs):
        """
        A subclass of GenericIndexer for interacting with the Jacket API.

        """
        super().__init__(name="jackett")
        config = AllEncompassingConfig().indexers.jackett
        self.api_key = config.api_key
        self.url = config.url
        self.indexers = config.indexers
        log.debug("Registering Jacket as Indexer")

    # NOTE: this could be done in parallel, but if there aren't more than a dozen indexers, it shouldn't matter
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
                responses.extend(future.result())

        return responses

    def get_torrents_by_indexer(
        self, indexer: str, query: str, is_tv: bool, session: requests.Session
    ) -> list[IndexerQueryResult]:
        download_volume_factor = 1.0  # Default value
        upload_volume_factor = 1  # Default value
        seeders = 0  # Default value

        url = (
            self.url
            + f"/api/v2.0/indexers/{indexer}/results/torznab/api?apikey={self.api_key}&t={'tvsearch' if is_tv else 'movie'}&q={query}"
        )
        response = session.get(url)

        if response.status_code != 200:
            log.error(
                f"Jacket error with indexer {indexer}, error: {response.status_code}"
            )
            return []

        result_list: list[IndexerQueryResult] = []
        xml_tree = ET.fromstring(response.content)
        xmlns = {
            "torznab": "http://torznab.com/schemas/2015/feed",
            "atom": "http://www.w3.org/2005/Atom",
        }
        for item in xml_tree.findall("channel/item"):
            attributes: list[Element] = [x for x in item.findall("torznab:attr", xmlns)]
            for attribute in attributes:
                if attribute.attrib["name"] == "seeders":
                    seeders = int(attribute.attrib["value"])
                if attribute.attrib["name"] == "downloadvolumefactor":
                    download_volume_factor = float(attribute.attrib["value"])
                if attribute.attrib["name"] == "uploadvolumefactor":
                    upload_volume_factor = int(attribute.attrib["value"])
            flags = []
            if download_volume_factor == 0:
                flags.append("freeleech")
            if download_volume_factor == 0.5:
                flags.append("halfleech")
            if download_volume_factor == 0.75:
                flags.append("freeleech75")
            if download_volume_factor == 0.25:
                flags.append("freeleech25")
            if upload_volume_factor == 2:
                flags.append("doubleupload")

            result = IndexerQueryResult(
                title=item.find("title").text,
                download_url=str(item.find("enclosure").attrib["url"]),
                seeders=seeders,
                flags=flags,
                size=int(item.find("size").text),
                usenet=False,  # always False, because Jackett doesn't support usenet
                age=0,  # always 0 for torrents, as Jackett does not provide age information in a convenient format
                indexer=item.find("jackettindexer").text
                if item.find("jackettindexer") is not None
                else None,
            )
            result_list.append(result)

        log.info(
            f"found {len(result_list)} results for query '{query}' from indexer '{indexer}'"
        )
        return result_list
