import logging

import qbittorrentapi
from qbittorrentapi import Conflict409Error

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstract_download_client import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus
from media_manager.torrent.utils import get_torrent_hash

log = logging.getLogger(__name__)


class QbittorrentDownloadClient(AbstractDownloadClient):
    name = "qbittorrent"

    DOWNLOADING_STATE = (
        "allocating",
        "downloading",
        "metaDL",
        "pausedDL",
        "queuedDL",
        "stalledDL",
        "checkingDL",
        "forcedDL",
        "moving",
        "stoppedDL",
        "forcedMetaDL",
        "metaDL",
    )
    FINISHED_STATE = (
        "uploading",
        "pausedUP",
        "queuedUP",
        "stalledUP",
        "checkingUP",
        "forcedUP",
        "stoppedUP",
    )
    ERROR_STATE = ("missingFiles", "error", "checkingResumeData")
    UNKNOWN_STATE = ("unknown",)

    def __init__(self) -> None:
        self.config = MediaManagerConfig().torrents.qbittorrent
        self.api_client = qbittorrentapi.Client(
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            username=self.config.username,
        )
        try:
            self.api_client.auth_log_in()
        except Exception:
            log.exception("Failed to log into qbittorrent")
            raise

        categories = self.api_client.torrents_categories()
        log.debug(f"Found following categories in qBittorrent: {categories}")
        if self.config.category_name in categories:
            category = categories.get(self.config.category_name)
            if category.get("savePath") == self.config.category_save_path:
                log.debug(
                    f"Category '{self.config.category_name}' already exists in qBittorrent with the correct save path."
                )
                return
            # category exists but with a different save path, attempt to update it
            log.debug(
                f"Category '{self.config.category_name}' already exists in qBittorrent but with a different save path. Attempting to update it."
            )
            try:
                self.api_client.torrents_edit_category(
                    name=self.config.category_name,
                    save_path=self.config.category_save_path,
                )
            except Conflict409Error:
                log.exception(
                    f"Attempt to update category '{self.config.category_name}' in qBittorrent with a different save"
                    f" path failed. The configured save path and the save path saved in Qbittorrent differ,"
                    f" manually update it in the qBittorrent WebUI or change the save path in the MediaManager"
                    f" config to match the one in qBittorrent."
                )
        else:
            # create category if it doesn't exist
            log.debug(
                f"Category '{self.config.category_name}' does not exist in qBittorrent. Attempting to create it."
            )
            try:
                self.api_client.torrents_create_category(
                    name=self.config.category_name,
                    save_path=self.config.category_save_path,
                )
            except Conflict409Error:
                log.exception(
                    f"Attempt to create category '{self.config.category_name}' in qBittorrent failed. The category already exists but was not found in the initial category list, manually check if the category exists in the qBittorrent WebUI or change the category name in the MediaManager config."
                )

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a torrent to the download client and return the torrent object.

        :param indexer_result: The indexer query result of the torrent file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        torrent_hash = get_torrent_hash(torrent=indexer_result)
        answer = None

        try:
            self.api_client.auth_log_in()
            answer = self.api_client.torrents_add(
                category="MediaManager",
                urls=indexer_result.download_url,
                save_path=indexer_result.title,
            )
        finally:
            self.api_client.auth_log_out()

        if answer != "Ok.":
            log.error(
                f"Failed to download torrent, API-Answer isn't 'Ok.'; API Answer: {answer}"
            )
            msg = f"Failed to download torrent, API-Answer isn't 'Ok.'; API Answer: {answer}"
            raise RuntimeError(msg)

        log.info(f"Successfully processed torrent: {indexer_result.title}")

        # Create and return torrent object
        torrent = Torrent(
            status=TorrentStatus.unknown,
            title=indexer_result.title,
            quality=indexer_result.quality,
            imported=False,
            hash=torrent_hash,
        )

        # Get initial status from download client
        torrent.status = self.get_torrent_status(torrent)

        return torrent

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a torrent from the download client.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded data.
        """
        log.info(f"Removing torrent: {torrent.title}")
        try:
            self.api_client.auth_log_in()
            self.api_client.torrents_delete(
                torrent_hashes=torrent.hash, delete_files=delete_data
            )
        finally:
            self.api_client.auth_log_out()

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific torrent.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        try:
            self.api_client.auth_log_in()
            info = self.api_client.torrents_info(torrent_hashes=torrent.hash)
        finally:
            self.api_client.auth_log_out()

        if not info:
            log.warning(f"No information found for torrent: {torrent.id}")
            return TorrentStatus.unknown
        state: str = info[0]["state"]

        if state in self.DOWNLOADING_STATE:
            return TorrentStatus.downloading
        if state in self.FINISHED_STATE:
            return TorrentStatus.finished
        if state in self.ERROR_STATE:
            return TorrentStatus.error
        if state in self.UNKNOWN_STATE:
            return TorrentStatus.unknown
        return TorrentStatus.error

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a torrent download.

        :param torrent: The torrent to pause.
        """
        try:
            self.api_client.auth_log_in()
            self.api_client.torrents_pause(torrent_hashes=torrent.hash)
        finally:
            self.api_client.auth_log_out()

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a torrent download.

        :param torrent: The torrent to resume.
        """
        try:
            self.api_client.auth_log_in()
            self.api_client.torrents_resume(torrent_hashes=torrent.hash)
        finally:
            self.api_client.auth_log_out()
