import logging
import pprint
import re
from pathlib import Path
from typing import Callable

from media_manager.common.service import BaseMediaService
from media_manager.config import MediaManagerConfig
from media_manager.metadataProvider.abstract_metadata_provider import AbstractMetadataProvider
from media_manager.notification.service import NotificationService
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.schemas import Quality, Torrent
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import get_files_for_import, import_file, remove_special_characters
from media_manager.tv.metadata import TvMetadataService
from media_manager.tv.repository import TvRepository
from media_manager.tv.schemas import Episode, EpisodeFile, Season, Show

log = logging.getLogger(__name__)


class TvImportService(BaseMediaService[Show, Show]):
    def __init__(
        self,
        tv_repository: TvRepository,
        torrent_service: TorrentService,
        notification_service: NotificationService,
        tv_metadata_service: TvMetadataService,
    ) -> None:
        super().__init__(
            repository=tv_repository,
            torrent_service=torrent_service,
            indexer_service=None,  # type: ignore
            notification_service=notification_service,
        )
        self.tv_repository = tv_repository
        self.tv_metadata_service = tv_metadata_service

    def get_root_show_directory(self, show: Show) -> Path:
        misc_config = MediaManagerConfig().misc
        return self.get_root_directory(
            media=show,
            default_dir=misc_config.tv_directory,
            libraries=misc_config.tv_libraries,
        )

    def get_root_season_directory(self, show: Show, season_number: int) -> Path:
        return self.get_root_show_directory(show) / Path(f"Season {season_number}")

    def import_episode(
        self,
        show: Show,
        season: Season,
        episode_number: int,
        video_files: list[Path],
        subtitle_files: list[Path],
        file_path_suffix: str = "",
    ) -> bool:
        episode_file_name = f"{remove_special_characters(show.name)} S{season.number:02d}E{episode_number:02d}"
        if file_path_suffix != "":
            episode_file_name += f" - {file_path_suffix}"
        pattern = (
            r".*[. ]S0?" + str(season.number) + r"E0?" + str(episode_number) + r"[. ].*"
        )
        subtitle_pattern = pattern + r"[. ]([A-Za-z]{2})[. ]srt"
        target_file_name = (
            self.get_root_season_directory(show=show, season_number=season.number)
            / episode_file_name
        )

        # import subtitle
        for subtitle_file in subtitle_files:
            regex_result = re.search(
                subtitle_pattern, subtitle_file.name, re.IGNORECASE
            )
            if regex_result:
                language_code = regex_result.group(1)
                target_subtitle_file = target_file_name.with_suffix(
                    f".{language_code}.srt"
                )
                import_file(target_file=target_subtitle_file, source_file=subtitle_file)
            else:
                log.debug(
                    f"Didn't find any pattern {subtitle_pattern} in subtitle file: {subtitle_file.name}"
                )

        # import episode videos
        for file in video_files:
            if re.search(pattern, file.name, re.IGNORECASE):
                target_video_file = target_file_name.with_suffix(file.suffix)
                import_file(target_file=target_video_file, source_file=file)
                return True
        else:
            msg = f"Could not find any video file for episode {episode_number} of show {show.name} S{season.number}"
            raise Exception(msg)  # noqa: TRY002 # TODO: resolve this

    def import_season(
        self,
        show: Show,
        season: Season,
        video_files: list[Path],
        subtitle_files: list[Path],
        file_path_suffix: str = "",
    ) -> tuple[bool, list[Episode]]:
        season_path = self.get_root_season_directory(
            show=show, season_number=season.number
        )
        success = True
        imported_episodes = []
        try:
            season_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.exception(f"Could not create path {season_path}")
            msg = f"Could not create path {season_path}"
            raise Exception(msg) from e  # noqa: TRY002 # TODO: resolve this

        for episode in season.episodes:
            try:
                imported = self.import_episode(
                    show=show,
                    subtitle_files=subtitle_files,
                    video_files=video_files,
                    season=season,
                    episode_number=episode.number,
                    file_path_suffix=file_path_suffix,
                )
                if imported:
                    imported_episodes.append(episode)

            except Exception:
                # Send notification about missing episode file
                if self.notification_service:
                    self.notification_service.send_notification_to_all_providers(
                        title="Missing Episode File",
                        message=f"No video file found for S{season.number:02d}E{episode.number:02d} for show {show.name}. Manual intervention may be required.",
                    )
                success = False
                log.warning(
                    f"S{season.number}E{episode.number} not found when trying to import episode for show {show.name}."
                )
        return success, imported_episodes

    def import_episode_files(
        self,
        show: Show,
        season: Season,
        episode: Episode,
        video_files: list[Path],
        subtitle_files: list[Path],
        file_path_suffix: str = "",
    ) -> bool:
        episode_file_name = f"{remove_special_characters(show.name)} S{season.number:02d}E{episode.number:02d}"
        if file_path_suffix != "":
            episode_file_name += f" - {file_path_suffix}"
        pattern = (
            r".*[. ]S0?" + str(season.number) + r"E0?" + str(episode.number) + r"[. ].*"
        )
        subtitle_pattern = pattern + r"[. ]([A-Za-z]{2})[. ]srt"
        target_file_name = (
            self.get_root_season_directory(show=show, season_number=season.number)
            / episode_file_name
        )

        # import subtitle
        for subtitle_file in subtitle_files:
            regex_result = re.search(
                subtitle_pattern, subtitle_file.name, re.IGNORECASE
            )
            if regex_result:
                language_code = regex_result.group(1)
                target_subtitle_file = target_file_name.with_suffix(
                    f".{language_code}.srt"
                )
                import_file(target_file=target_subtitle_file, source_file=subtitle_file)
            else:
                log.debug(
                    f"Didn't find any pattern {subtitle_pattern} in subtitle file: {subtitle_file.name}"
                )

        found_video = False

        # import episode videos
        for file in video_files:
            if re.search(pattern, file.name, re.IGNORECASE):
                target_video_file = target_file_name.with_suffix(file.suffix)
                import_file(target_file=target_video_file, source_file=file)
                found_video = True
                break

        if not found_video:
            # Send notification about missing episode file
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Missing Episode File",
                    message=f"No video file found for S{season.number:02d}E{episode.number:02d} for show {show.name}. Manual intervention may be required.",
                )
            log.warning(
                f"File for S{season.number}E{episode.number} not found when trying to import episode for show {show.name}."
            )
            return False

        return True

    def import_episode_files_from_torrent(self, torrent: Torrent, show: Show) -> None:
        """
        Organizes episodes files from a torrent into the TV directory structure, mapping them to seasons and episodes.
        :param torrent: The Torrent object
        :param show: The Show object
        """

        video_files, subtitle_files, _all_files = get_files_for_import(torrent=torrent)

        success: list[bool] = []

        log.debug(
            f"Importing these {len(video_files)} files:\n" + pprint.pformat(video_files)
        )

        episode_files = self.torrent_service.get_episode_files_of_torrent(
            torrent=torrent
        )
        if not episode_files:
            log.warning(
                f"No episode files associated with torrent {torrent.title}, skipping import."
            )
            return

        log.info(
            f"Found {len(episode_files)} episode files associated with torrent {torrent.title}"
        )

        imported_episodes_by_season: dict[int, list[int]] = {}

        for episode_file in episode_files:
            season = self.tv_repository.get_season_by_episode(episode_id=episode_file.episode_id)
            episode = self.tv_repository.get_episode(episode_id=episode_file.episode_id)

            season_path = self.get_root_season_directory(
                show=show, season_number=season.number
            )
            if not season_path.exists():
                try:
                    season_path.mkdir(parents=True)
                except Exception as e:
                    log.warning(f"Could not create path {season_path}: {e}")
                    msg = f"Could not create path {season_path}"
                    raise Exception(msg) from e  # noqa: TRY002

            episoded_import_success = self.import_episode_files(
                show=show,
                season=season,
                episode=episode,
                video_files=video_files,
                subtitle_files=subtitle_files,
                file_path_suffix=episode_file.file_path_suffix,
            )
            success.append(episoded_import_success)

            if episoded_import_success:
                imported_episodes_by_season.setdefault(season.number, []).append(
                    episode.number
                )

                log.info(
                    f"Episode {episode.number} from Season {season.number} successfully imported from torrent {torrent.title}"
                )
            else:
                log.warning(
                    f"Episode {episode.number} from Season {season.number} failed to import from torrent {torrent.title}"
                )

        success_messages: list[str] = []

        for season_number, episodes in imported_episodes_by_season.items():
            episode_list = ",".join(str(e) for e in sorted(episodes))
            success_messages.append(
                f"Episode(s): {episode_list} from Season {season_number}"
            )

        episodes_summary = "; ".join(success_messages)

        if all(success):
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)

            # Send successful season download notification
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="TV Show imported successfully",
                    message=(
                        f"Successfully imported {episodes_summary} "
                        f"of {show.name} ({show.year}) "
                        f"from torrent {torrent.title}."
                    ),
                )
        else:
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Failed to import TV Show",
                    message=f"Importing {show.name} ({show.year}) from torrent {torrent.title} completed with errors. Please check the logs for details.",
                )

        log.info(
            f"Finished importing files for torrent {torrent.title} {'without' if all(success) else 'with'} errors"
        )

    def get_import_candidates(
        self, tv_show: Path, metadata_provider: AbstractMetadataProvider
    ) -> MediaImportSuggestion:
        return super().get_import_candidates(
            directory=tv_show,
            metadata_provider=metadata_provider,
            search_func=self.tv_metadata_service.search_for_show,
        )

    def import_existing_tv_show(self, tv_show: Show, source_directory: Path) -> bool:
        def _import_logic(s: Show, path: Path, add_record_cb: Callable[[EpisodeFile], None]) -> bool:
            video_files, subtitle_files, _all_files = get_files_for_import(directory=path)
            for season in s.seasons:
                _success, imported_episodes = self.import_season(
                    show=s,
                    season=season,
                    video_files=video_files,
                    subtitle_files=subtitle_files,
                    file_path_suffix="IMPORTED",
                )
                for episode in imported_episodes:
                    add_record_cb(
                        EpisodeFile(
                            episode_id=episode.id,
                            quality=Quality.unknown,
                            file_path_suffix="IMPORTED",
                            torrent_id=None,
                        )
                    )
            return True

        return self.import_existing_media(
            media=tv_show,
            source_directory=source_directory,
            import_func=_import_logic,
            add_file_record_func=self.tv_repository.add_episode_file,
        )

    def get_importable_tv_shows(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MediaImportSuggestion]:
        return self.get_importable_media(
            root_path=MediaManagerConfig().misc.tv_directory,
            metadata_provider=metadata_provider,
            get_candidates_func=self.get_import_candidates,
        )

    def import_all_torrents(self) -> None:
        self.import_all_torrents_base(
            get_media_func=self.torrent_service.get_show_of_torrent,
            import_torrent_func=self.import_episode_files_from_torrent,
            media_type_name="tv",
        )
