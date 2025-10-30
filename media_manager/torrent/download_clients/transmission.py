import logging

import transmission_rpc
from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstractDownloadClient import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import TorrentStatus, Torrent
from media_manager.torrent.utils import get_torrent_hash

log = logging.getLogger(__name__)


class TransmissionDownloadClient(AbstractDownloadClient):
    name = "transmission"

    # Transmission status mappings
    STATUS_MAPPING = {
        "stopped": TorrentStatus.unknown,
        "check pending": TorrentStatus.downloading,
        "checking": TorrentStatus.downloading,
        "download pending": TorrentStatus.downloading,
        "downloading": TorrentStatus.downloading,
        "seed pending": TorrentStatus.finished,
        "seeding": TorrentStatus.finished,
    }

    def __init__(self):
        self.config = AllEncompassingConfig().torrents.transmission
        try:
            self._client = transmission_rpc.Client(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                protocol="https" if self.config.https_enabled else "http",
                path=self.config.path,
            )
            # Test connection
            self._client.session_stats()
            log.info("Successfully connected to Transmission")
        except Exception as e:
            log.error(f"Failed to connect to Transmission: {e}")
            raise

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a torrent to the Transmission client and return the torrent object.

        :param indexer_result: The indexer query result of the torrent file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        log.info(f"Attempting to download torrent: {indexer_result.title}")
        torrent_hash = get_torrent_hash(torrent=indexer_result)
        log.info(f"parsed torrent hash: {torrent_hash}")
        download_dir = (
            AllEncompassingConfig().misc.torrent_directory / indexer_result.title
        )
        try:
            self._client.add_torrent(
                torrent=str(indexer_result.download_url),
                download_dir=str(download_dir),
            )

            log.info(
                f"Successfully added torrent to Transmission: {indexer_result.title}"
            )

        except Exception as e:
            log.error(f"Failed to add torrent to Transmission: {e}")
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

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a torrent from the Transmission client.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded data.
        """
        log.info(f"Removing torrent: {torrent.title}")

        try:
            self._client.remove_torrent(torrent.hash, delete_data=delete_data)
            log.info(f"Successfully removed torrent: {torrent.title}")
        except Exception as e:
            log.error(f"Failed to remove torrent: {e}")
            raise

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific torrent.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        log.debug(f"Fetching status for torrent: {torrent.title}")

        try:
            transmission_torrent = self._client.get_torrent(torrent.hash)

            if transmission_torrent is None:
                log.warning(f"Torrent not found in Transmission: {torrent.hash}")
                return TorrentStatus.unknown

            status = self.STATUS_MAPPING.get(
                transmission_torrent.status, TorrentStatus.unknown
            )

            if transmission_torrent.error != 0:
                status = TorrentStatus.error
                log.warning(
                    f"Torrent {torrent.title} has error status: {transmission_torrent.error_string}"
                )

            log.debug(f"Torrent {torrent.title} status: {status}")
            return status

        except Exception as e:
            log.error(f"Failed to get torrent status: {e}")
            return TorrentStatus.error

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a torrent download.

        :param torrent: The torrent to pause.
        """
        log.info(f"Pausing torrent: {torrent.title}")

        try:
            self._client.stop_torrent(torrent.hash)
            log.info(f"Successfully paused torrent: {torrent.title}")

        except Exception as e:
            log.error(f"Failed to pause torrent: {e}")
            raise

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a torrent download.

        :param torrent: The torrent to resume.
        """
        log.info(f"Resuming torrent: {torrent.title}")

        try:
            self._client.start_torrent(torrent.hash)
            log.info(f"Successfully resumed torrent: {torrent.title}")

        except Exception as e:
            log.error(f"Failed to resume torrent: {e}")
            raise
