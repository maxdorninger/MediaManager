import logging

from media_manager.indexer.schemas import IndexerQueryResult
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

log = logging.getLogger(__name__)


class TorznabMixin:
    def process_search_result(self, xml: str) -> list[IndexerQueryResult]:
        result_list: list[IndexerQueryResult] = []
        xml_tree = ET.fromstring(xml)
        xmlns = {
            "torznab": "http://torznab.com/schemas/2015/feed",
            "atom": "http://www.w3.org/2005/Atom",
        }
        for item in xml_tree.findall("channel/item"):
            try:
                flags = []
                seeders = 0
                age = 0
                indexer_name = "unknown"

                if item.find("jackettindexer") is not None:
                    indexer_name = item.find("jackettindexer").text
                if item.find("prowlarrindexer") is not None:
                    indexer_name = item.find("prowlarrindexer").text

                is_usenet = (
                    item.find("enclosure").attrib["type"] != "application/x-bittorrent"
                )

                attributes = list(item.findall("torznab:attr", xmlns))
                for attribute in attributes:
                    if is_usenet:
                        if attribute.attrib["name"] == "usenetdate":
                            posted_date = parsedate_to_datetime(
                                attribute.attrib["value"]
                            )
                            now = datetime.now(timezone.utc)
                            age = int((now - posted_date).total_seconds())
                    else:
                        if attribute.attrib["name"] == "seeders":
                            seeders = int(attribute.attrib["value"])

                        if attribute.attrib["name"] == "downloadvolumefactor":
                            download_volume_factor = float(attribute.attrib["value"])
                            if download_volume_factor == 0:
                                flags.append("freeleech")
                            if download_volume_factor == 0.5:
                                flags.append("halfleech")
                            if download_volume_factor == 0.75:
                                flags.append("freeleech75")
                            if download_volume_factor == 0.25:
                                flags.append("freeleech25")

                        if attribute.attrib["name"] == "uploadvolumefactor":
                            upload_volume_factor = int(attribute.attrib["value"])
                            if upload_volume_factor == 2:
                                flags.append("doubleupload")

                result = IndexerQueryResult(
                    title=item.find("title").text,
                    download_url=str(item.find("enclosure").attrib["url"]),
                    seeders=seeders,
                    flags=flags,
                    size=int(item.find("size").text),
                    usenet=is_usenet,
                    age=age,
                    indexer=indexer_name,
                )
                result_list.append(result)
            except Exception as e:
                log.error(f"1 Torznab search result errored with error: {e}")
        return result_list
