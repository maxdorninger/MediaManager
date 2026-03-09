import hashlib
import logging

import bencoder
import libtorrent
import requests
from pathvalidate import sanitize_filename
from requests.exceptions import InvalidSchema

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.indexer.utils import follow_redirects_to_final_torrent_url

log = logging.getLogger(__name__)


def get_torrent_hash(torrent: IndexerQueryResult) -> str:
    """
    Helper method to get the torrent hash from the torrent object.

    :param torrent: The torrent object.
    :return: The hash of the torrent.
    """
    torrent_filepath = (
        MediaManagerConfig().misc.torrent_directory
        / f"{sanitize_filename(torrent.title)}.torrent"
    )
    if torrent_filepath.exists():
        log.warning(f"Torrent file already exists at: {torrent_filepath}")

    if torrent.download_url.startswith("magnet:"):
        log.info(f"Parsing torrent with magnet URL: {torrent.title}")
        log.debug(f"Magnet URL: {torrent.download_url}")
        torrent_hash = str(libtorrent.parse_magnet_uri(torrent.download_url).info_hash)
    else:
        # downloading the torrent file
        log.info(f"Downloading .torrent file of torrent: {torrent.title}")
        try:
            response = requests.get(str(torrent.download_url), timeout=30)
            response.raise_for_status()
            torrent_content = response.content
        except InvalidSchema:
            log.debug(f"Invalid schema for URL {torrent.download_url}", exc_info=True)
            final_url = follow_redirects_to_final_torrent_url(
                initial_url=torrent.download_url,
                session=requests.Session(),
                timeout=MediaManagerConfig().indexers.prowlarr.timeout_seconds,
            )
            return str(libtorrent.parse_magnet_uri(final_url).info_hash)
        except Exception:
            log.exception("Failed to download torrent file")
            raise

        # saving the torrent file
        torrent_filepath.write_bytes(torrent_content)

        # parsing info hash
        log.debug(f"parsing torrent file: {torrent.download_url}")
        try:
            decoded_content = bencoder.decode(torrent_content)
            torrent_hash = hashlib.sha1(  # noqa: S324
                bencoder.encode(decoded_content[b"info"])
            ).hexdigest()
        except Exception:
            log.exception("Failed to decode torrent file")
            raise

    return torrent_hash


