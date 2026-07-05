import logging
import shutil
import time
import xmlrpc.client
from urllib.parse import quote

import pyrosimple
import requests
from requests.exceptions import InvalidSchema

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.indexer.utils import follow_redirects_to_final_torrent_url
from media_manager.torrent.download_clients.abstract_download_client import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus
from media_manager.torrent.utils import get_torrent_filepath, get_torrent_hash

log = logging.getLogger(__name__)

# rTorrent loads torrents asynchronously, so wait for the download to register
# before returning (callers may immediately pause/query it by info-hash).
_REGISTRATION_TIMEOUT_SECONDS = 15.0
_REGISTRATION_POLL_SECONDS = 0.5


class RtorrentDownloadClient(AbstractDownloadClient):
    name = "rtorrent"

    def __init__(self) -> None:
        self.config = MediaManagerConfig().torrents.rtorrent

        scheme = "https" if self.config.https_enabled else "http"
        credentials = ""
        if self.config.username:
            credentials = f"{quote(self.config.username)}:{quote(self.config.password)}@"
        path = self.config.path if self.config.path.startswith("/") else f"/{self.config.path}"
        url = f"{scheme}://{credentials}{self.config.host}:{self.config.port}{path}"

        try:
            self._engine = pyrosimple.connect(url)
            # Test connection
            self._engine.rpc.system.client_version()
        except Exception:
            log.exception("Failed to connect to rTorrent")
            raise

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a torrent to the rTorrent client and return the torrent object.

        :param indexer_result: The indexer query result of the torrent file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        torrent_hash = get_torrent_hash(torrent=indexer_result)
        download_dir = (
            MediaManagerConfig().misc.torrent_directory / indexer_result.title
        )
        try:
            # Load the torrent stopped, then configure and start it. The download
            # directory and label are passed as proper XML-RPC arguments (not
            # embedded in load command strings) so that values coming from the
            # indexer (e.g. the title) cannot break out or inject commands.
            self._load(indexer_result)
            # rTorrent registers the download asynchronously.
            self._wait_until_registered(torrent_hash)

            target_hash = torrent_hash.upper()
            self._engine.rpc.d.directory.set(target_hash, str(download_dir))
            self._engine.rpc.d.custom1.set(target_hash, self.config.label)
            self._engine.rpc.d.start(target_hash)

            log.info(f"Successfully added torrent to rTorrent: {indexer_result.title}")
        except Exception:
            log.exception("Failed to add torrent to rTorrent")
            raise

        torrent = Torrent(
            status=TorrentStatus.unknown,
            title=indexer_result.title,
            quality=indexer_result.quality,
            imported=False,
            hash=torrent_hash,
            usenet=False,
        )

        torrent.status = self.get_torrent_status(torrent)

        return torrent

    def _load(self, indexer_result: IndexerQueryResult) -> None:
        """
        Load a torrent into rTorrent in a stopped state.

        Unlike qBittorrent/Transmission, rTorrent cannot follow an HTTP redirect
        to a magnet link, so the download URL is resolved here (mirroring
        get_torrent_hash): magnet links are loaded as-is, .torrent files are
        downloaded and pushed as raw data. Loading stopped lets the caller set
        the download directory before the download starts.
        """
        download_url = str(indexer_result.download_url)
        if download_url.startswith("magnet:"):
            self._engine.rpc.load.normal("", download_url)
            return

        try:
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
        except InvalidSchema:
            # The URL redirected to a magnet link, which requests cannot fetch.
            magnet = follow_redirects_to_final_torrent_url(
                initial_url=indexer_result.download_url,
                session=requests.Session(),
                timeout=MediaManagerConfig().indexers.prowlarr.timeout_seconds,
            )
            self._engine.rpc.load.normal("", magnet)
            return

        self._engine.rpc.load.raw("", xmlrpc.client.Binary(response.content))

    def _wait_until_registered(self, torrent_hash: str) -> None:
        """
        Wait until rTorrent has registered the download for the given hash.

        :raises RuntimeError: If the download does not register before the timeout.
        """
        target_hash = torrent_hash.upper()
        deadline = time.monotonic() + _REGISTRATION_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            try:
                if target_hash in self._engine.rpc.download_list():
                    return
            except Exception:
                log.debug("Failed to fetch download list while waiting", exc_info=True)
            time.sleep(_REGISTRATION_POLL_SECONDS)
        msg = (
            f"Torrent {target_hash} did not register in rTorrent within "
            f"{_REGISTRATION_TIMEOUT_SECONDS}s"
        )
        raise RuntimeError(msg)

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a torrent from the rTorrent client.

        rTorrent does not delete downloaded files on erase, so when requested the
        download directory is removed from the (shared) filesystem afterwards.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded data.
        """
        try:
            self._engine.rpc.d.erase(torrent.hash.upper())
        except Exception:
            log.exception("Failed to remove torrent")
            raise

        if delete_data:
            download_dir = get_torrent_filepath(torrent=torrent)
            try:
                shutil.rmtree(download_dir)
            except FileNotFoundError:
                log.debug(f"Download directory not found, nothing to delete: {download_dir}")
            except OSError:
                log.exception(f"Failed to delete download directory: {download_dir}")

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific torrent.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        torrent_hash = torrent.hash.upper()
        try:
            # d.complete raises an XML-RPC fault if the hash is unknown to rTorrent
            try:
                complete = self._engine.rpc.d.complete(torrent_hash)
            except Exception:
                log.warning(f"Torrent not found in rTorrent: {torrent_hash}")
                return TorrentStatus.unknown

            # Check completion first: a finished torrent must always import, even
            # if it still carries a benign tracker message.
            if int(complete) == 1:
                return TorrentStatus.finished

            message = self._engine.rpc.d.message(torrent_hash)
            if message and "Tried all trackers" not in message:
                log.warning(f"Torrent {torrent.title} has error message: {message}")
                return TorrentStatus.error
        except Exception:
            log.exception("Failed to get torrent status")
            return TorrentStatus.error

        return TorrentStatus.downloading

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a torrent download.

        :param torrent: The torrent to pause.
        """
        try:
            self._engine.rpc.d.pause(torrent.hash.upper())
            log.debug(f"Successfully paused torrent: {torrent.title}")
        except Exception:
            log.exception("Failed to pause torrent")
            raise

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a torrent download.

        :param torrent: The torrent to resume.
        """
        try:
            self._engine.rpc.d.resume(torrent.hash.upper())
            log.debug(f"Successfully resumed torrent: {torrent.title}")
        except Exception:
            log.exception("Failed to resume torrent")
            raise
