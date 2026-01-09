import logging
from enum import Enum

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstract_download_client import (
    AbstractDownloadClient,
)
from media_manager.torrent.download_clients.qbittorrent import QbittorrentDownloadClient
from media_manager.torrent.download_clients.sabnzbd import SabnzbdDownloadClient
from media_manager.torrent.download_clients.transmission import (
    TransmissionDownloadClient,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus

log = logging.getLogger(__name__)


class DownloadClientType(Enum):
    """Types of download clients supported"""

    TORRENT = "torrent"
    USENET = "usenet"


class DownloadManager:
    """
    Manages download clients and routes downloads to the appropriate client
    based on the content type (torrent vs usenet).
    Only one torrent client and one usenet client are active at a time.
    """

    def __init__(self) -> None:
        self._torrent_client: AbstractDownloadClient | None = None
        self._usenet_client: AbstractDownloadClient | None = None
        self.config = MediaManagerConfig().torrents
        self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize and register the default download clients"""

        # Initialize torrent clients (prioritize qBittorrent, fallback to Transmission)
        if self.config.qbittorrent.enabled:
            try:
                self._torrent_client = QbittorrentDownloadClient()
            except Exception as e:
                log.error(f"Failed to initialize qBittorrent client: {e}")

        # If qBittorrent is not available or failed, try Transmission
        if self._torrent_client is None and self.config.transmission.enabled:
            try:
                self._torrent_client = TransmissionDownloadClient()
            except Exception as e:
                log.error(f"Failed to initialize Transmission client: {e}")

        # Initialize SABnzbd client for usenet
        if self.config.sabnzbd.enabled:
            try:
                self._usenet_client = SabnzbdDownloadClient()
            except Exception as e:
                log.error(f"Failed to initialize SABnzbd client: {e}")

        active_clients = []
        if self._torrent_client:
            active_clients.append(f"torrent ({self._torrent_client.name})")
        if self._usenet_client:
            active_clients.append(f"usenet ({self._usenet_client.name})")

    def _get_appropriate_client(
        self, indexer_result: IndexerQueryResult | Torrent
    ) -> AbstractDownloadClient:
        """
        Select the appropriate download client based on the indexer result

        :param indexer_result: The indexer query result to determine client type
        :return: The appropriate download client
        :raises RuntimeError: If no suitable client is available
        """
        # Use the usenet flag from the indexer result to determine the client type
        if indexer_result.usenet:
            if not self._usenet_client:
                msg = "No usenet download client configured"
                raise RuntimeError(msg)
            return self._usenet_client
        if not self._torrent_client:
            msg = "No torrent download client configured"
            raise RuntimeError(msg)
        return self._torrent_client

    def download(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Download content using the appropriate client

        :param indexer_result: The indexer query result to download
        :return: The torrent object representing the download
        """
        log.info(f"Processing download request for: {indexer_result.title}")

        client = self._get_appropriate_client(indexer_result)
        return client.download_torrent(indexer_result)

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a torrent using the appropriate client

        :param torrent: The torrent to remove
        :param delete_data: Whether to delete the downloaded data
        """
        log.info(f"Removing torrent: {torrent.title}")

        client = self._get_appropriate_client(torrent)
        client.remove_torrent(torrent, delete_data)

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a torrent using the appropriate client

        :param torrent: The torrent to get status for
        :return: The current status of the torrent
        """
        client = self._get_appropriate_client(torrent)
        return client.get_torrent_status(torrent)

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a torrent using the appropriate client

        :param torrent: The torrent to pause
        """
        log.info(f"Pausing torrent: {torrent.title}")

        client = self._get_appropriate_client(torrent)
        client.pause_torrent(torrent)

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a torrent using the appropriate client

        :param torrent: The torrent to resume
        """
        log.info(f"Resuming torrent: {torrent.title}")

        client = self._get_appropriate_client(torrent)
        client.resume_torrent(torrent)
