import shutil
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from media_manager.common.service import BaseMediaService
from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.indexer.service import IndexerService
from media_manager.indexer.utils import evaluate_indexer_query_results
from media_manager.notification.service import NotificationService
from media_manager.torrent.schemas import (
    Torrent,
)
from media_manager.torrent.service import TorrentService
from media_manager.tv import log
from media_manager.tv.importer import TvImportService
from media_manager.tv.metadata import TvMetadataService
from media_manager.tv.repository import TvRepository
from media_manager.tv.schemas import (
    Episode,
    EpisodeFile,
    EpisodeId,
    EpisodeNumber,
    PublicEpisodeFile,
    PublicSeason,
    PublicShow,
    RichSeasonTorrent,
    RichShowTorrent,
    Season,
    SeasonId,
    Show,
    ShowId,
)


class TvService(BaseMediaService[Show, Show]):
    def __init__(
        self,
        tv_repository: TvRepository,
        torrent_service: TorrentService,
        indexer_service: IndexerService,
        notification_service: NotificationService,
        tv_import_service: TvImportService,
        tv_metadata_service: TvMetadataService,
    ) -> None:
        super().__init__(
            repository=tv_repository,
            torrent_service=torrent_service,
            indexer_service=indexer_service,
            notification_service=notification_service,
        )
        self.tv_repository = tv_repository
        self.tv_import_service = tv_import_service
        self.tv_metadata_service = tv_metadata_service

    def get_total_downloaded_episodes_count(self) -> int:
        """
        Get total number of downloaded episodes.
        """

        return self.tv_repository.get_total_downloaded_episodes_count()

    def set_show_library(self, show: Show, library: str) -> None:
        self.tv_repository.set_show_library(show.id, library)

    def get_all_shows(self) -> list[Show]:
        """
        Get all shows in the library.
        """
        return self.get_all_media()

    def delete_show(
        self,
        show: Show,
        delete_files_on_disk: bool = False,
        delete_torrents: bool = False,
    ) -> None:
        """
        Delete a show from the database, optionally deleting files and torrents.

        :param show: The show to delete.
        :param delete_files_on_disk: Whether to delete the show's files from disk.
        :param delete_torrents: Whether to delete associated torrents from the torrent client.
        """
        if delete_files_on_disk or delete_torrents:
            log.debug(f"Deleting ID: {show.id} - Name: {show.name}")

            if delete_files_on_disk:
                show_dir = self.get_root_show_directory(show=show)

                log.debug(f"Attempt to delete show directory: {show_dir}")
                if show_dir.exists() and show_dir.is_dir():
                    shutil.rmtree(show_dir)
                    log.info(f"Deleted show directory: {show_dir}")

            if delete_torrents:
                torrents = self.tv_repository.get_torrents_by_show_id(show_id=show.id)
                for torrent in torrents:
                    try:
                        self.torrent_service.cancel_download(torrent, delete_files=True)
                        self.torrent_service.delete_torrent(torrent_id=torrent.id)
                        log.info(f"Deleted torrent: {torrent.hash}")
                    except Exception:
                        log.warning(
                            f"Failed to delete torrent {torrent.hash}", exc_info=True
                        )

        self.tv_repository.delete_show(show.id)

    def get_public_episode_files_by_season_id(
        self, season: Season
    ) -> list[PublicEpisodeFile]:
        """
        Get all public episode files for a given season.

        :param season: The season object.
        :return: A list of public episode files.
        """
        episode_files = self.tv_repository.get_episode_files_by_season_id(
            season_id=season.id
        )
        public_episode_files = [
            PublicEpisodeFile.model_validate(x) for x in episode_files
        ]
        result = []
        for episode_file in public_episode_files:
            if self.episode_file_exists_on_file(episode_file=episode_file):
                episode_file.downloaded = True
            result.append(episode_file)
        return result

    def get_all_available_torrents_for_a_season(
        self,
        season_number: int,
        show_id: ShowId,
        search_query_override: str | None = None,
    ) -> list[IndexerQueryResult]:
        """
        Get all available torrents for a given season.

        :param season_number: The number of the season.
        :param show_id: The ID of the show.
        :param search_query_override: Optional override for the search query.
        :return: A list of indexer query results.
        """

        if search_query_override:
            return self.indexer_service.search(query=search_query_override, is_tv=True)

        show = self.tv_repository.get_show_by_id(show_id=show_id)

        torrents = self.indexer_service.search_season(
            show=show, season_number=season_number
        )

        results = [torrent for torrent in torrents if season_number in torrent.season]

        return evaluate_indexer_query_results(
            is_tv=True, query_results=results, media=show
        )

    def get_public_show_by_id(self, show: Show) -> PublicShow:
        """
        Get a public show from a Show object.

        :param show: The show object.
        :return: A public show.
        """
        public_show = PublicShow.model_validate(show)
        public_seasons: list[PublicSeason] = []

        for season in show.seasons:
            public_season = PublicSeason.model_validate(season)

            for episode in public_season.episodes:
                episode.downloaded = self.is_episode_downloaded(
                    episode=episode,
                    season=season,
                    show=show,
                )

            # A season is considered downloaded if it has episodes and all of them are downloaded,
            # matching the behavior of is_season_downloaded.
            public_season.downloaded = bool(public_season.episodes) and all(
                episode.downloaded for episode in public_season.episodes
            )
            public_seasons.append(public_season)

        public_show.seasons = public_seasons
        return public_show

    def get_show_by_id(self, show_id: ShowId) -> Show:
        """
        Get a show by its ID.

        :param show_id: The ID of the show.
        :return: The show.
        """
        return self.tv_repository.get_show_by_id(show_id=show_id)

    def is_season_downloaded(self, season: Season, show: Show) -> bool:
        """
        Check if a season is downloaded.

        :param season: The season object.
        :param show: The show object.
        :return: True if the season is downloaded, False otherwise.
        """
        episodes = season.episodes

        if not episodes:
            return False

        for episode in episodes:
            if not self.is_episode_downloaded(
                episode=episode, season=season, show=show
            ):
                return False
        return True

    def is_episode_downloaded(
        self, episode: Episode, season: Season, show: Show
    ) -> bool:
        """
        Check if an episode is downloaded and imported (file exists on disk).

        An episode is considered downloaded if:
        - There is at least one EpisodeFile in the database AND
        - A matching episode file exists in the season directory on disk.

        :param episode: The episode object.
        :param season: The season object.
        :param show: The show object.
        :return: True if the episode is downloaded and imported, False otherwise.
        """
        episode_files = self.tv_repository.get_episode_files_by_episode_id(
            episode_id=episode.id
        )

        if not episode_files:
            return False

        season_dir = self.get_root_season_directory(show, season.number)

        if not season_dir.exists():
            return False

        episode_token = f"S{season.number:02d}E{episode.number:02d}"

        video_extensions = {".mkv", ".mp4", ".avi", ".mov"}

        try:
            for file in season_dir.iterdir():
                if (
                    file.is_file()
                    and episode_token.lower() in file.name.lower()
                    and file.suffix.lower() in video_extensions
                ):
                    return True

        except OSError as e:
            log.error(
                f"Disk check failed for episode {episode.id} in {season_dir}: {e}"
            )

        return False

    def episode_file_exists_on_file(self, episode_file: EpisodeFile) -> bool:
        """
        Check if an episode file exists on the filesystem.

        :param episode_file: The episode file to check.
        :return: True if the file exists, False otherwise.
        """
        if episode_file.torrent_id is None:
            return True
        try:
            torrent_file = self.torrent_service.get_torrent_by_id(
                torrent_id=episode_file.torrent_id
            )

            if torrent_file.imported:
                return True
        except RuntimeError:
            log.exception("Error retrieving torrent")

        return False

    def get_show_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> Show | None:
        """
        Get a show by its external ID and metadata provider.

        :param external_id: The external ID of the show.
        :param metadata_provider: The metadata provider.
        :return: The show or None if not found.
        """
        return self.tv_repository.get_show_by_external_id(
            external_id=external_id, metadata_provider=metadata_provider
        )

    def get_season(self, season_id: SeasonId) -> Season:
        """
        Get a season by its ID.

        :param season_id: The ID of the season.
        :return: The season.
        """
        return self.tv_repository.get_season(season_id=season_id)

    def get_episode(self, episode_id: EpisodeId) -> Episode:
        """
        Get an episode by its ID.

        :param episode_id: The ID of the episode.
        :return: The episode.
        """
        return self.tv_repository.get_episode(episode_id=episode_id)

    def get_season_by_episode(self, episode_id: EpisodeId) -> Season:
        """
        Get a season by the episode ID.

        :param episode_id: The ID of the episode.
        :return: The season.
        """
        return self.tv_repository.get_season_by_episode(episode_id=episode_id)

    def get_torrents_for_show(self, show: Show) -> RichShowTorrent:
        """
        Get torrents for a given show.

        :param show: The show.
        :return: A rich show torrent.
        """
        show_torrents = self.tv_repository.get_torrents_by_show_id(show_id=show.id)
        rich_season_torrents = []
        for show_torrent in show_torrents:
            seasons = self.tv_repository.get_seasons_by_torrent_id(
                torrent_id=show_torrent.id
            )
            episodes = self.tv_repository.get_episodes_by_torrent_id(
                torrent_id=show_torrent.id
            )
            episode_files = self.torrent_service.get_episode_files_of_torrent(
                torrent=show_torrent
            )

            file_path_suffix = (
                episode_files[0].file_path_suffix if episode_files else ""
            )
            season_torrent = RichSeasonTorrent(
                torrent_id=show_torrent.id,
                torrent_title=show_torrent.title,
                status=show_torrent.status,
                quality=show_torrent.quality,
                imported=show_torrent.imported,
                seasons=seasons,
                episodes=episodes if len(seasons) == 1 else [],
                file_path_suffix=file_path_suffix,
                usenet=show_torrent.usenet,
            )
            rich_season_torrents.append(season_torrent)

        return RichShowTorrent(
            show_id=show.id,
            name=show.name,
            year=show.year,
            metadata_provider=show.metadata_provider,
            torrents=rich_season_torrents,
        )

    def get_all_shows_with_torrents(self) -> list[RichShowTorrent]:
        """
        Get all shows with torrents.

        :return: A list of rich show torrents.
        """
        shows = self.tv_repository.get_all_shows_with_torrents()
        return [self.get_torrents_for_show(show=show) for show in shows]

    def download_torrent(
        self,
        public_indexer_result_id: IndexerQueryResultId,
        show_id: ShowId,
        override_show_file_path_suffix: str = "",
    ) -> Torrent:
        """
        Download a torrent for a given indexer result and show.

        :param public_indexer_result_id: The ID of the indexer result.
        :param show_id: The ID of the show.
        :param override_show_file_path_suffix: Optional override for the file path suffix.
        :return: The downloaded torrent.
        """
        indexer_result = self.indexer_service.get_result(
            result_id=public_indexer_result_id
        )
        show_torrent = self.torrent_service.download(indexer_result=indexer_result)
        self.torrent_service.pause_download(torrent=show_torrent)

        try:
            for season_number in indexer_result.season:
                season = self.tv_repository.get_season_by_number(
                    season_number=season_number, show_id=show_id
                )
                episodes = {episode.number: episode.id for episode in season.episodes}

                if indexer_result.episode:
                    episode_ids = []
                    missing_episodes = []
                    for ep_number in indexer_result.episode:
                        ep_id = episodes.get(EpisodeNumber(ep_number))
                        if ep_id is None:
                            missing_episodes.append(ep_number)
                            continue
                        episode_ids.append(ep_id)
                    if missing_episodes:
                        log.warning(
                            "Some episodes from indexer result were not found in season %s "
                            "for show %s and will be skipped: %s",
                            season.id,
                            show_id,
                            ", ".join(str(ep) for ep in missing_episodes),
                        )
                else:
                    episode_ids = [episode.id for episode in season.episodes]

                for episode_id in episode_ids:
                    episode_file = EpisodeFile(
                        episode_id=episode_id,
                        quality=indexer_result.quality,
                        torrent_id=show_torrent.id,
                        file_path_suffix=override_show_file_path_suffix,
                    )
                    self.tv_repository.add_episode_file(episode_file=episode_file)

        except IntegrityError:
            log.error(
                f"Episode file for episode {episode_id} of season {season.id} and quality {indexer_result.quality} already exists, skipping."
            )
            self.tv_repository.remove_episode_files_by_torrent_id(show_torrent.id)
            self.torrent_service.cancel_download(
                torrent=show_torrent, delete_files=True
            )
            raise
        else:
            log.info(
                f"Successfully added episode files for torrent {show_torrent.title} and show ID {show_id}"
            )
            self.torrent_service.resume_download(torrent=show_torrent)

        return show_torrent

    def get_root_show_directory(self, show: Show) -> Path:
        misc_config = MediaManagerConfig().misc
        return self.get_root_directory(
            media=show,
            default_dir=misc_config.tv_directory,
            libraries=misc_config.tv_libraries,
        )

    def get_root_season_directory(self, show: Show, season_number: int) -> Path:
        return self.get_root_show_directory(show) / Path(f"Season {season_number}")

    def set_show_continuous_download(
        self, show: Show, continuous_download: bool
    ) -> Show:
        """
        Set the continuous download flag for a show.

        :param show: The show object.
        :param continuous_download: True to enable continuous download, False to disable.
        :return: The updated Show object.
        """
        return self.tv_repository.update_show_attributes(
            show_id=show.id, continuous_download=continuous_download
        )

    def import_all_torrents(self) -> None:
        """
        Delegate to TvImportService.
        """
        self.tv_import_service.import_all_torrents()

    def update_all_non_ended_shows_metadata(self) -> None:
        """
        Delegate to TvMetadataService.
        """
        self.tv_metadata_service.update_all_non_ended_shows_metadata()
