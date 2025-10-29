import logging

from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.manager import DownloadManager
from media_manager.torrent.repository import TorrentRepository
from media_manager.torrent.schemas import Torrent, TorrentId
from media_manager.tv.schemas import SeasonFile, Show
from media_manager.movies.schemas import Movie

log = logging.getLogger(__name__)


class TorrentService:
    def __init__(
        self,
        torrent_repository: TorrentRepository,
        download_manager: DownloadManager = None,
    ):
        self.torrent_repository = torrent_repository
        self.download_manager = download_manager or DownloadManager()

    def get_season_files_of_torrent(self, torrent: Torrent) -> list[SeasonFile]:
        """
        Returns all season files of a torrent
        :param torrent: the torrent to get the season files of
        :return: list of season files
        """
        return self.torrent_repository.get_seasons_files_of_torrent(
            torrent_id=torrent.id
        )

    def get_show_of_torrent(self, torrent: Torrent) -> Show | None:
        """
        Returns the show of a torrent
        :param torrent: the torrent to get the show of
        :return: the show of the torrent
        """
        return self.torrent_repository.get_show_of_torrent(torrent_id=torrent.id)

    def get_movie_of_torrent(self, torrent: Torrent) -> Movie | None:
        """
        Returns the movie of a torrent
        :param torrent: the torrent to get the movie of
        :return: the movie of the torrent
        """
        return self.torrent_repository.get_movie_of_torrent(torrent_id=torrent.id)

    def download(self, indexer_result: IndexerQueryResult) -> Torrent:
        log.info(f"Attempting to download torrent: {indexer_result.title}")

        torrent = self.download_manager.download(indexer_result)

        return self.torrent_repository.save_torrent(torrent=torrent)

    def get_torrent_status(self, torrent: Torrent) -> Torrent:
        log.info(f"Fetching status for torrent: {torrent.title}")

        torrent.status = self.download_manager.get_torrent_status(torrent)

        self.torrent_repository.save_torrent(torrent=torrent)
        return torrent

    def cancel_download(self, torrent: Torrent, delete_files: bool = False) -> Torrent:
        """
        cancels download of a torrent

        :param delete_files: Deletes the downloaded files of the torrent too, deactivated by default
        :param torrent: the torrent to cancel
        """
        log.info(f"Cancelling download for torrent: {torrent.title}")
        self.download_manager.remove_torrent(torrent, delete_data=delete_files)
        return self.get_torrent_status(torrent=torrent)

    def pause_download(self, torrent: Torrent) -> Torrent:
        """
        pauses download of a torrent

        :param torrent: the torrent to pause
        """
        log.info(f"Pausing download for torrent: {torrent.title}")
        self.download_manager.pause_torrent(torrent)
        return self.get_torrent_status(torrent=torrent)

    def resume_download(self, torrent: Torrent) -> Torrent:
        """
        resumes download of a torrent

        :param torrent: the torrent to resume
        """
        log.info(f"Resuming download for torrent: {torrent.title}")
        self.download_manager.resume_torrent(torrent)
        return self.get_torrent_status(torrent=torrent)

    def get_all_torrents(self) -> list[Torrent]:
        torrents = []
        for x in self.torrent_repository.get_all_torrents():
            try:
                torrents.append(self.get_torrent_status(x))
            except RuntimeError as e:
                log.error(f"Error fetching status for torrent {x.title}: {e}")
        return torrents

    def get_torrent_by_id(self, torrent_id: TorrentId) -> Torrent:
        return self.get_torrent_status(
            self.torrent_repository.get_torrent_by_id(torrent_id=torrent_id)
        )

    def delete_torrent(self, torrent_id: TorrentId):
        t = self.torrent_repository.get_torrent_by_id(torrent_id=torrent_id)
        self.torrent_repository.delete_torrent(torrent_id=t.id)

    def get_movie_files_of_torrent(self, torrent: Torrent):
        return self.torrent_repository.get_movie_files_of_torrent(torrent_id=torrent.id)
