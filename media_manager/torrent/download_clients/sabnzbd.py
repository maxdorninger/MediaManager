import logging

import sabnzbd_api

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstract_download_client import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus

log = logging.getLogger(__name__)


class SabnzbdDownloadClient(AbstractDownloadClient):
    name = "sabnzbd"

    DOWNLOADING_STATE = (
        "Downloading",
        "Queued",
        "Paused",
        "Extracting",
        "Moving",
        "Running",
    )
    FINISHED_STATE = ("Completed",)
    ERROR_STATE = ("Failed",)
    UNKNOWN_STATE = ("Unknown",)

    def __init__(self) -> None:
        self.config = MediaManagerConfig().torrents.sabnzbd
        self.client = sabnzbd_api.SabnzbdClient(
            host=self.config.host,
            port=str(self.config.port),
            api_key=self.config.api_key,
        )
        self.client._base_url = f"{self.config.host.rstrip('/')}:{self.config.port}{self.config.base_path}"  # the library expects a /sabnzbd prefix for whatever reason
        try:
            # Test connection
            self.client.version()
        except Exception:
            log.exception("Failed to connect to SABnzbd")
            raise

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a NZB/torrent to SABnzbd and return the torrent object.

        :param indexer_result: The indexer query result of the NZB file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        try:
            # Add NZB to SABnzbd queue
            response = self.client.add_uri(
                url=str(indexer_result.download_url), nzbname=indexer_result.title
            )
            if not response["status"]:
                raise RuntimeError(f"Failed to add NZB to SABnzbd: {response}")  # noqa: EM102, TRY003, TRY301

            # Generate a hash for the NZB (using title and download URL)
            nzo_id = response["nzo_ids"][0]

            # Create and return torrent object
            torrent = Torrent(
                status=TorrentStatus.unknown,
                title=indexer_result.title,
                quality=indexer_result.quality,
                imported=False,
                hash=nzo_id,
                usenet=True,
            )

            # Get initial status from SABnzbd
            torrent.status = self.get_torrent_status(torrent)
        except Exception:
            log.exception(f"Failed to download NZB {indexer_result.title}")
            raise

        return torrent

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a torrent from SABnzbd.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded files.
        """
        try:
            self.client.delete_job(nzo_id=torrent.hash, delete_files=delete_data)
        except Exception:
            log.exception(f"Failed to remove torrent {torrent.title}")
            raise

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a torrent in SABnzbd.

        :param torrent: The torrent to pause.
        """
        try:
            self.client.pause_job(nzo_id=torrent.hash)
        except Exception:
            log.exception(f"Failed to pause torrent {torrent.title}")
            raise

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a paused torrent in SABnzbd.

        :param torrent: The torrent to resume.
        """
        try:
            self.client.resume_job(nzo_id=torrent.hash)
        except Exception:
            log.exception(f"Failed to resume torrent {torrent.title}")
            raise

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific download from SABnzbd.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        response = self.client.get_downloads(nzo_ids=torrent.hash)
        status = response["queue"]["status"]
        return self._map_status(status)

    def _map_status(self, sabnzbd_status: str) -> TorrentStatus:
        """
        Map SABnzbd status to TorrentStatus.

        :param sabnzbd_status: The status from SABnzbd.
        :return: The corresponding TorrentStatus.
        """
        if sabnzbd_status in self.DOWNLOADING_STATE:
            return TorrentStatus.downloading
        if sabnzbd_status in self.FINISHED_STATE:
            return TorrentStatus.finished
        if sabnzbd_status in self.ERROR_STATE:
            return TorrentStatus.error
        return TorrentStatus.unknown
