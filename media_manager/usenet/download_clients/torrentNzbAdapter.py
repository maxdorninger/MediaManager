"""
Adapts Torrent objects to Nzb objects, and vice versa.

Allows for Usenet functions to be partially abstracted from Torrent functions,
pending a full breakout.
"""
import logging
from media_manager.usenet.schemas import Nzb, NzbStatus
from media_manager.torrent.schemas import Torrent, TorrentStatus

log = logging.getLogger(__name__)

class TorrentNzbAdapter:
    name = "TorrentNzbAdapter"

    @staticmethod
    def nzb_to_torrent(nzb: Nzb) -> Torrent:
        """
        Convert a Nzb object to a Torrent object.

        :param nzb: The Nzb object to convert.
        :return: The converted Torrent object.
        """
        log.debug(f"Converting Nzb to Torrent: {nzb}")
        status = TorrentNzbAdapter.convert_status(nzb.status) if nzb.status else TorrentStatus.unknown
        torrent = Torrent(
            status=status,
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
        log.debug(f"Converting Torrent to Nzb: {torrent}")
        status = TorrentNzbAdapter.convert_status(torrent.status) if torrent.status else NzbStatus.unknown
        nzb = Nzb(
            status=status,
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
        log.debug(f"Converting status object {status_obj} of type {type(status_obj)}")
        log.debug(f"status object value is {status_obj.value}")
        if isinstance(status_obj, NzbStatus) and status_obj.value == 5:
            return TorrentStatus(2)
        elif isinstance(status_obj, NzbStatus):
            return TorrentStatus(status_obj.value)
        elif isinstance(status_obj, TorrentStatus) :
            return NzbStatus(status_obj.value)

