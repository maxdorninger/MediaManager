import logging

from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.usenet.schemas import (
    Nzb,
    NzbStatus,
    sabnzbd_to_nzb_status
)

import sabnzbd_api

log = logging.getLogger(__name__)


class SabnzbdDownloadClient:
    name = "sabnzbd"

    def __init__(self):
        self.config = AllEncompassingConfig().torrents.sabnzbd
        self.client = sabnzbd_api.SabnzbdClient(
            host=self.config.host,
            port=str(self.config.port),
            api_key=self.config.api_key,
        )
        self.client._base_url = f"{self.config.host.rstrip('/')}:{self.config.port}{self.config.base_path}"  # the library expects a /sabnzbd prefix for whatever reason
        try:
            # Test connection
            version = self.client.version()

            log.info(f"Successfully connected to SABnzbd version: {version}")
        except Exception as e:
            log.error(f"Failed to connect to SABnzbd: {e}")
            raise

    def download_nzb(self, indexer_result: IndexerQueryResult) -> Nzb:
        """
        Add a NZB to SABnzbd and return the Nzb object.

        :param indexer_result: The indexer query result of the NZB file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        log.info(f"Attempting to download NZB: {indexer_result.title}")

        try:
            # Add NZB to SABnzbd queue
            response = self.client.add_uri(
                url=str(indexer_result.download_url), nzbname=indexer_result.title
            )
            if not response["status"]:
                error_msg = response
                log.error(f"Failed to add NZB to SABnzbd: {error_msg}")
                raise RuntimeError(f"Failed to add NZB to SABnzbd: {error_msg}")

            # Generate a hash for the NZB (using title and download URL)
            nzo_id = response["nzo_ids"][0]

            log.info(f"Successfully added NZB: {indexer_result.title}")

            # Create and return torrent object
            nzb = Nzb(
                status=NzbStatus.unknown,
                title=indexer_result.title,
                quality=indexer_result.quality,
                imported=False,
                hash=nzo_id,
            )

            # Get initial status from SABnzbd
            nzb.status = self.get_nzb_status(nzb)

            return nzb

        except Exception as e:
            log.error(f"Failed to download NZB {indexer_result.title}: {e}")
            raise

    def remove_nzb(self, nzb: Nzb, delete_data: bool = False) -> None:
        """
        Remove a nzb from SABnzbd.

        :param nzb: The nzb to remove.
        :param delete_data: Whether to delete the downloaded files.
        """
        log.info(f"Removing nzb: {nzb.title} (Delete data: {delete_data})")
        try:
            self.client.delete_job(nzo_id=nzb.hash, delete_files=delete_data)
            log.info(f"Successfully removed nzb: {nzb.title}")
        except Exception as e:
            log.error(f"Failed to remove nzb {nzb.title}: {e}")
            raise

    def pause_nzb(self, nzb: Nzb) -> None:
        """
        Pause a nzb in SABnzbd.

        :param nzb: The nzb to pause.
        """
        log.info(f"Pausing nzb: {nzb.title}")
        try:
            self.client.pause_job(nzo_id=nzb.hash)
            log.info(f"Successfully paused nzb: {nzb.title}")
        except Exception as e:
            log.error(f"Failed to pause nzb {nzb.title}: {e}")
            raise

    def resume_nzb(self, nzb: Nzb) -> None:
        """
        Resume a paused nzb in SABnzbd.

        :param nzb: The nzb to resume.
        """
        log.info(f"Resuming nzb: {nzb.title}")
        try:
            self.client.resume_job(nzo_id=nzb.hash)
            log.info(f"Successfully resumed nzb: {nzb.title}")
        except Exception as e:
            log.error(f"Failed to resume nzb {nzb.title}: {e}")
            raise


    def get_nzb_status(self, nzb: Nzb) -> NzbStatus:
        """
        Get the status of a specific download from SABnzbd.

        :param nzb: The nzb to get the status of.
        :return: The status of the nzb.
        """
        # Check the queue for in progress downloads
        status = self._get_in_progress_status(nzb)
        if status is not NzbStatus.unknown:
            return status
        # Check the history for processing or completed downloads
        status = self._get_finished_status(nzb)
        if status is not NzbStatus.unknown:
            return status

        log.warning(f"Could not find any downloads for nzb: {nzb.title}")
        return status

    def _get_in_progress_status(self, nzb: Nzb) -> NzbStatus:
        """
        Check SABnzbd in progress downloads for torrent status.

        :param torrent: The torrent for which to get the status.
        """
        log.info(f"Checking in progress downloads for status: {nzb.title}")
        response = self.client.get_downloads(nzo_ids=nzb.hash)
        log.debug("SABnzbd queue response: %s", response)
        nzb_slots = response["queue"]["slots"]
        if len(nzb_slots) >= 1:
            status = nzb_slots[0]["status"]
            log.info(f"Status for in progress nzb {nzb.title}: {status}")
            return sabnzbd_to_nzb_status(status)

        log.info(f"Didn't find any downloads in progress for nzb: {nzb.title}")
        return NzbStatus.unknown

    def _get_finished_status(self, nzb: Nzb) -> NzbStatus:
        """
        Check SABnzbd finished downloads for nzb status.

        :param nzb: The nzb for which to get the status.
        """
        log.info(f"Checking completed downloads for status: {nzb.title}")
        response = self.client.get_history(nzo_ids=nzb.hash)
        log.debug("SABnzbd history response: %s", response)
        nzb_slots = response["history"]["slots"]
        if len(nzb_slots) >= 1:
            status = nzb_slots[0]["status"]
            log.info(f"Status for downloaded nzb {nzb.title}: {status}")
            return sabnzbd_to_nzb_status(status)

        log.info(f"Didn't find any completed downloads for nzb: {nzb.title}")
        return NzbStatus.unknown
