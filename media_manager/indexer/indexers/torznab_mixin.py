import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

from media_manager.indexer.schemas import IndexerQueryResult

log = logging.getLogger(__name__)


class TorznabMixin:
    def process_search_result(self, xml: str) -> list[IndexerQueryResult]:
        result_list: list[IndexerQueryResult] = []
        xml_tree = ET.fromstring(xml)  # noqa: S314  # trusted source, since it is user controlled
        xmlns = {
            "torznab": "http://torznab.com/schemas/2015/feed",
            "atom": "http://www.w3.org/2005/Atom",
        }
        for item in xml_tree.findall("channel/item"):
            try:
                result = self._process_item(item, xmlns)
                if result:
                    result_list.append(result)
            except Exception:
                log.exception("1 Torznab search result failed")
        return result_list

    def _process_item(self, item: ET.Element, xmlns: dict) -> IndexerQueryResult | None:
        indexer_name = "unknown"
        if item.find("jackettindexer") is not None:
            indexer_name = item.find("jackettindexer").text or "unknown"
        elif item.find("prowlarrindexer") is not None:
            indexer_name = item.find("prowlarrindexer").text or "unknown"

        is_usenet = item.find("enclosure").attrib["type"] != "application/x-bittorrent"

        seeders, age, flags = self._parse_torznab_attributes(item, xmlns, is_usenet)

        title = item.find("title").text or "unknown"
        size_str = item.find("size")
        if size_str is None or size_str.text is None:
            log.warning(f"Torznab item {title} has no size, skipping.")
            return None

        try:
            size = int(size_str.text or "0")
        except ValueError:
            log.warning(f"Torznab item {title} has invalid size, skipping.")
            return None

        return IndexerQueryResult(
            title=title,
            download_url=str(item.find("enclosure").attrib["url"]),
            seeders=seeders,
            flags=flags,
            size=size,
            usenet=is_usenet,
            age=age,
            indexer=indexer_name,
        )

    def _parse_torznab_attributes(
        self, item: ET.Element, xmlns: dict, is_usenet: bool
    ) -> tuple[int, int, list[str]]:
        seeders = 0
        age = 0
        flags = []
        attributes = list(item.findall("torznab:attr", xmlns))
        for attribute in attributes:
            name = attribute.attrib["name"]
            value = attribute.attrib["value"]
            if is_usenet:
                if name == "usenetdate":
                    posted_date = parsedate_to_datetime(value)
                    now = datetime.now(datetime.UTC)
                    age = int((now - posted_date).total_seconds())
            else:
                if name == "seeders":
                    seeders = int(value)
                elif name == "downloadvolumefactor":
                    self._add_leech_flags(float(value), flags)
                elif name == "uploadvolumefactor":
                    if int(value) == 2:
                        flags.append("doubleupload")
        return seeders, age, flags

    def _add_leech_flags(self, factor: float, flags: list[str]) -> None:
        if factor == 0:
            flags.append("freeleech")
        elif factor == 0.5:
            flags.append("halfleech")
        elif factor == 0.75:
            flags.append("freeleech75")
        elif factor == 0.25:
            flags.append("freeleech25")
