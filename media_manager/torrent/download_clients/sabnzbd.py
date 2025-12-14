from media_manager.torrent.download_clients.abstractDownloadClient import (
    AbstractDownloadClient,
)
from media_manager.usenet.download_clients.torrentNzbAdapter import TorrentNzbAdapter
from media_manager.usenet.download_clients.sabnzbd import SabnzbdDownloadClient as SabnzbdUsenetDownloadClient
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.schemas import Torrent, TorrentStatus

class SabnzbdDownloadClient(AbstractDownloadClient):
    """
    Sabnzbd download client abiding by the abstract download client.

    Converts calls to/from compatible calls with usenet.download_clients.sabnzbd.SabnzbdDownloadClient. This allows the
    Sabnzbd download client to exist with Usenet/Nzb-first logic, while still only being partially abstracted from the
    torrent-first functionality.
    """
    name = "sabnzbd"

    def __init__(self):
        self.usenet = SabnzbdUsenetDownloadClient()

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """
        Add a NZB/torrent to SABnzbd and return the torrent object.

        :param indexer_result: The indexer query result of the NZB file to download.
        :return: The torrent object with calculated hash and initial status.
        """
        nzb = self.usenet.download_nzb(indexer_result)
        return TorrentNzbAdapter.nzb_to_torrent(nzb)


    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        """
        Remove a torrent from SABnzbd.

        :param torrent: The torrent to remove.
        :param delete_data: Whether to delete the downloaded files.
        """
        nzb = TorrentNzbAdapter.torrent_to_nzb(torrent)
        self.usenet.remove_nzb(nzb, delete_data)

    def pause_torrent(self, torrent: Torrent) -> None:
        """
        Pause a torrent in SABnzbd.

        :param torrent: The torrent to pause.
        """
        nzb = TorrentNzbAdapter.torrent_to_nzb(torrent)
        self.usenet.pause_nzb(nzb)

    def resume_torrent(self, torrent: Torrent) -> None:
        """
        Resume a paused torrent in SABnzbd.

        :param torrent: The torrent to resume.
        """
        nzb = TorrentNzbAdapter.torrent_to_nzb(torrent)
        return self.usenet.resume_nzb(nzb)

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """
        Get the status of a specific download from SABnzbd.

        :param torrent: The torrent to get the status of.
        :return: The status of the torrent.
        """
        nzb = TorrentNzbAdapter.torrent_to_nzb(torrent)
        status = self.usenet.get_nzb_status(nzb)
        return TorrentNzbAdapter.convert_status(status)
