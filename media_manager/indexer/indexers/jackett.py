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
        self.timeout_seconds = config.timeout_seconds

    def search(
        self,
        query: str,
        is_tv: bool,
        imdb_id: str | None = None,
        season: int | None = None,
    ) -> list[IndexerQueryResult]:

        log.debug("Searching for " + query)

        futures = []
        with ThreadPoolExecutor() as executor, requests.Session() as session:
            for indexer in self.indexers:
                future = executor.submit(
                    self.get_torrents_by_indexer, indexer, query, is_tv, session, imdb_id, season
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
        self,
        indexer: str,
        query: str,
        is_tv: bool,
        session: requests.Session,
        imdb_id: str | None = None,
        season: int | None = None
    ) -> list[IndexerQueryResult]:
        download_volume_factor = 1.0  # Default value
        upload_volume_factor = 1  # Default value
        seeders = 0  # Default value

        if imdb_id:
            log.debug(f"Searching Prowlarr by IMDB ID: '{imdb_id}'")
            query_str = f"imdbid={imdb_id}"
        else:
            log.debug(f"Searching Prowlarr for query: '{query}'")
            query_str = f"q={query}"

        if is_tv:
            cat = "t=tvsearch&cat=5000"
            if season is not None:
                query_str = f"{query_str}&season={season}"
        else:
            cat = "t=movie&cat=2000"

        url = (
            self.url
            + f"/api/v2.0/indexers/{indexer}/results/torznab/api?apikey={self.api_key}&{query_str}&{cat}"
        )
        response = session.get(url, timeout=self.timeout_seconds)

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
            try:
                attributes: list[Element] = [
                    x for x in item.findall("torznab:attr", xmlns)
                ]
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
            except Exception as e:
                log.error(
                    f"1 Jackett search result errored with indexer {indexer}, error: {e}"
                )

        log.info(
            f"found {len(result_list)} results for query '{query}' from indexer '{indexer}'"
        )
        return result_list
