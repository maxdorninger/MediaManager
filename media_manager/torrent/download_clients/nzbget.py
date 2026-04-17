import logging

import requests

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstract_download_client import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus

log = logging.getLogger(__name__)


class NzbgetDownloadClient(AbstractDownloadClient):
    name = "nzbget"

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
    FINISHED_STATE = ("SUCCESS",)
    ERROR_STATE = ("FAILURE",)

    def __init__(self) -> None:
        self.config = MediaManagerConfig().torrents.nzbget
        scheme = "https" if self.config.use_https else "http"
        self._base_url = f"{scheme}://{self.config.host}:{self.config.port}"
        self._auth = (self.config.username, self.config.password)
        try:
            self._call("version")
        except Exception:
            log.exception("Failed to connect to NZBGet")
            raise

    def _call(self, method: str, params: list | None = None) -> object:
        """
        Make a JSON-RPC call to NZBGet.

        :param method: The API method name.
        :param params: Optional list of positional parameters.
        :return: The 'result' field of the JSON-RPC response.
        """
        url = f"{self._base_url}/jsonrpc"
        payload: dict = {"method": method, "id": 1}
        if params is not None:
            payload["params"] = params

        response = requests.post(url, json=payload, auth=self._auth, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data and data["error"] is not None:
            msg = f"NZBGet API error: {data['error']}"
            raise RuntimeError(msg)

        return data.get("result")

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a NZB to NZBGet and return the torrent object.

        :param indexer_result: The indexer query result of the NZB file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        try:
            # NZBGet append params:
            # NZBFilename, Content (base64 or empty), Category, Priority,
            # AddToTop, AddPaused, DupeKey, DupeScore, DupeMode, PPParameters
            nzb_id = self._call(
                "append",
                [
                    indexer_result.title + ".nzb",  # NZBFilename
                    str(indexer_result.download_url),  # Content (URL when no base64)
                    "",  # Category
                    0,  # Priority (normal)
                    False,  # AddToTop
                    False,  # AddPaused
                    "",  # DupeKey
                    0,  # DupeScore
                    "SCORE",  # DupeMode
                    [],  # PPParameters
                ],
            )

            if not nzb_id or nzb_id <= 0:
                msg = f"Failed to add NZB to NZBGet: returned id {nzb_id}"
                raise RuntimeError(msg)  # noqa: TRY301

            torrent = Torrent(
                status=TorrentStatus.unknown,
                title=indexer_result.title,
                quality=indexer_result.quality,
                imported=False,
                hash=str(nzb_id),
                usenet=True,
            )

            torrent.status = self.get_torrent_status(torrent)
        except Exception:
            log.exception(f"Failed to download NZB {indexer_result.title}")
            raise

        return torrent

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a download from NZBGet.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded files.
        """
        try:
            nzb_id = int(torrent.hash)
            # Try removing from queue first
            result = self._call("editqueue", ["GroupDelete", "", [nzb_id]])
            if not result:
                # If not in queue, try removing from history
                self._call("editqueue", ["HistoryDelete", "", [nzb_id]])
        except Exception:
            log.exception(f"Failed to remove torrent {torrent.title}")
            raise

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a download in NZBGet.

        :param torrent: The torrent to pause.
        """
        try:
            nzb_id = int(torrent.hash)
            self._call("editqueue", ["GroupPause", "", [nzb_id]])
        except Exception:
            log.exception(f"Failed to pause torrent {torrent.title}")
            raise

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a paused download in NZBGet.

        :param torrent: The torrent to resume.
        """
        try:
            nzb_id = int(torrent.hash)
            self._call("editqueue", ["GroupResume", "", [nzb_id]])
        except Exception:
            log.exception(f"Failed to resume torrent {torrent.title}")
            raise

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific download from NZBGet.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        nzb_id = int(torrent.hash)

        # Check active queue first
        groups = self._call("listgroups")
        if isinstance(groups, list):
            for group in groups:
                if group.get("NZBID") == nzb_id:
                    return self._map_status(group.get("Status", "UNKNOWN"))

        # Check history for completed/failed items
        history = self._call("history")
        if isinstance(history, list):
            for item in history:
                if item.get("NZBID") == nzb_id:
                    return self._map_status(item.get("Status", "UNKNOWN"))

        return TorrentStatus.unknown

    def _map_status(self, nzbget_status: str) -> TorrentStatus:
        """
        Map NZBGet status to TorrentStatus.

        :param nzbget_status: The status from NZBGet.
        :return: The corresponding TorrentStatus.
        """
        if nzbget_status in self.DOWNLOADING_STATE:
            return TorrentStatus.downloading
        if nzbget_status in self.FINISHED_STATE:
            return TorrentStatus.finished
        if nzbget_status in self.ERROR_STATE:
            return TorrentStatus.error
        return TorrentStatus.unknown
