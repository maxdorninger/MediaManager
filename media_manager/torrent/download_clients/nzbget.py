import logging

from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstractDownloadClient import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus
import pynzbgetapi

log = logging.getLogger(__name__)


class NzbgetDownloadClient(AbstractDownloadClient):
    name = "nzbget"

    # NZBGet status mappings
    # See: https://nzbget.com/documentation/api/listgroups/
    DOWNLOADING_STATE = (
        "QUEUED",
        "PAUSED",
        "DOWNLOADING",
        "FETCHING",
        "PP_QUEUED",
        "LOADING_PARS",
        "VERIFYING_SOURCES",
        "REPAIRING",
        "VERIFYING_REPAIRED",
        "RENAMING",
        "UNPACKING",
        "MOVING",
        "EXECUTING_SCRIPT",
    )
    FINISHED_STATE = ("PP_FINISHED",)
    ERROR_STATE = ("PP_ERROR",)

    def __init__(self):
        self.config = AllEncompassingConfig().torrents.nzbget
        protocol = "https" if self.config.use_https else "http"
        host_url = f"{protocol}://{self.config.host}:{self.config.port}"

        self.client = pynzbgetapi.NZBGetAPI(
            host_url,
            self.config.username,
            self.config.password,
        )

        try:
            # Test connection
            version = self.client.version()
            log.info(f"Successfully connected to NZBGet version: {version}")
        except Exception as e:
            log.error(f"Failed to connect to NZBGet: {e}")
            raise

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a NZB to NZBGet and return the torrent object.

        :param indexer_result: The indexer query result of the NZB file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        log.info(f"Attempting to download NZB: {indexer_result.title}")

        try:
            # Add NZB to NZBGet queue using URL
            # append(NZBFilename, Content, Category, Priority, AddToTop, AddPaused, DupeKey, DupeScore, DupeMode, PPParameters)
            # When Content is a URL, NZBFilename can be empty
            nzb_id = self.client.append(
                "",  # NZBFilename - empty when using URL
                str(indexer_result.download_url),  # Content - URL to fetch NZB from
                "",  # Category
                0,  # Priority (0 = normal)
                False,  # AddToTop
                False,  # AddPaused
                "",  # DupeKey
                0,  # DupeScore
                "SCORE",  # DupeMode
                [],  # PPParameters
            )

            if not nzb_id or nzb_id <= 0:
                error_msg = f"NZBGet returned invalid ID: {nzb_id}"
                log.error(f"Failed to add NZB to NZBGet: {error_msg}")
                raise RuntimeError(f"Failed to add NZB to NZBGet: {error_msg}")

            log.info(
                f"Successfully added NZB: {indexer_result.title} with ID: {nzb_id}"
            )

            # Create and return torrent object
            # Use the NZBGet ID as the hash
            torrent = Torrent(
                status=TorrentStatus.unknown,
                title=indexer_result.title,
                quality=indexer_result.quality,
                imported=False,
                hash=str(nzb_id),
                usenet=True,
            )

            # Get initial status from NZBGet
            torrent.status = self.get_torrent_status(torrent)

            return torrent

        except Exception as e:
            log.error(f"Failed to download NZB {indexer_result.title}: {e}")
            raise

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a download from NZBGet.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded files.
        """
        log.info(f"Removing download: {torrent.title} (Delete data: {delete_data})")
        try:
            nzb_id = int(torrent.hash)
            # editqueue(Command, Offset, EditText, IDs)
            # GroupDelete command removes the group from queue
            self.client.editqueue("GroupDelete", 0, "", [nzb_id])
            log.info(f"Successfully removed download: {torrent.title}")
        except Exception as e:
            log.error(f"Failed to remove download {torrent.title}: {e}")
            raise

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a download in NZBGet.

        :param torrent: The torrent to pause.
        """
        log.info(f"Pausing download: {torrent.title}")
        try:
            nzb_id = int(torrent.hash)
            # GroupPause command pauses the group
            self.client.editqueue("GroupPause", 0, "", [nzb_id])
            log.info(f"Successfully paused download: {torrent.title}")
        except Exception as e:
            log.error(f"Failed to pause download {torrent.title}: {e}")
            raise

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a paused download in NZBGet.

        :param torrent: The torrent to resume.
        """
        log.info(f"Resuming download: {torrent.title}")
        try:
            nzb_id = int(torrent.hash)
            # GroupResume command resumes the group
            self.client.editqueue("GroupResume", 0, "", [nzb_id])
            log.info(f"Successfully resumed download: {torrent.title}")
        except Exception as e:
            log.error(f"Failed to resume download {torrent.title}: {e}")
            raise

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific download from NZBGet.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        log.info(f"Fetching status for download: {torrent.title}")
        try:
            nzb_id = int(torrent.hash)
            groups = self.client.listgroups()

            for group in groups:
                if group.get("NZBID") == nzb_id:
                    status = group.get("Status", "UNKNOWN")
                    log.info(f"Download status for NZB {torrent.title}: {status}")
                    return self._map_status(status)

            # If not found in active queue, check history
            history = self.client.history()
            for item in history:
                if item.get("NZBID") == nzb_id:
                    status = item.get("Status", "UNKNOWN")
                    log.info(
                        f"Download status for NZB {torrent.title} (from history): {status}"
                    )
                    return self._map_history_status(status)

            log.warning(f"Download not found in NZBGet: {torrent.title}")
            return TorrentStatus.unknown

        except Exception as e:
            log.error(f"Failed to get status for {torrent.title}: {e}")
            return TorrentStatus.unknown

    def _map_status(self, nzbget_status: str) -> TorrentStatus:
        """
        Map NZBGet queue status to TorrentStatus.

        :param nzbget_status: The status from NZBGet.
        :return: The corresponding TorrentStatus.
        """
        if nzbget_status in self.DOWNLOADING_STATE:
            return TorrentStatus.downloading
        elif nzbget_status in self.FINISHED_STATE:
            return TorrentStatus.finished
        elif nzbget_status in self.ERROR_STATE:
            return TorrentStatus.error
        else:
            return TorrentStatus.unknown

    def _map_history_status(self, history_status: str) -> TorrentStatus:
        """
        Map NZBGet history status to TorrentStatus.
        History statuses are different from queue statuses.

        :param history_status: The status from NZBGet history.
        :return: The corresponding TorrentStatus.
        """
        # History statuses: SUCCESS, FAILURE, DELETED, etc.
        if history_status.startswith("SUCCESS"):
            return TorrentStatus.finished
        elif history_status.startswith("FAILURE"):
            return TorrentStatus.error
        elif history_status == "DELETED":
            return TorrentStatus.unknown
        else:
            return TorrentStatus.unknown
