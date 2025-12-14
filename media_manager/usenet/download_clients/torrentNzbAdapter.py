"""
Adapts Torrent objects to Nzb objects, and vice versa.

Allows for Usenet functions to be partially abstracted from Torrent functions,
pending a full breakout.
"""
from media_manager.usenet.schemas import Nzb, NzbStatus
from media_manager.torrent.schemas import Torrent, TorrentStatus


class TorrentNzbAdapter:
    @staticmethod
    def nzb_to_torrent(nzb: Nzb) -> Torrent:
        """
        Convert a Nzb object to a Torrent object.

        :param nzb: The Nzb object to convert.
        :return: The converted Torrent object.
        """
        torrent = Torrent(
            status=TorrentNzbAdapter.convert_status(nzb.status),
            title=nzb.title,
            quality=nzb.quality,
            imported=nzb.imported,
            hash=nzb.hash,
            usenet=True,
        )

        return torrent

    @staticmethod
    def torrent_to_nzb(torrent: Torrent) -> Nzb:
        """
        Convert a Torrent object to Nzb object.

        :param torrent: The Torrent object to convert.
        :return: The converted Nzb object.
        """
        nzb = Nzb(
            status=TorrentNzbAdapter.convert_status(torrent.status),
            title=torrent.title,
            quality=torrent.quality,
            imported=torrent.imported,
            hash=torrent.hash,
        )

        return nzb

    @staticmethod
    def convert_status(status_obj: NzbStatus or TorrentStatus) -> NzbStatus or TorrentStatus:
        """
        Converts NzbStatus to TorrentStatus or vice versa. NzbStatus 5 (processing) is folded
        into TorrentStatus 2 (downloading).

        :param status_obj: The NzbStatus or TorrentStatus object to convert.
        :return: The converted NzbStatus or TorrentStatus object.
        """
        if status_obj is NzbStatus and status_obj.value == 5:
            return TorrentStatus(2)
        elif status_obj is NzbStatus:
            return TorrentStatus(status_obj.value)
        elif status_obj is TorrentStatus:
            return NzbStatus(status_obj.value)

