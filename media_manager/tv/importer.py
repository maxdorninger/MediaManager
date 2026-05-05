import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from media_manager.common.service import BaseMediaService
from media_manager.config import MediaManagerConfig
from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.notification.service import NotificationService
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.schemas import Quality, Torrent
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import (
    get_files_for_import,
    get_torrent_filepath,
    import_file,
    remove_special_characters,
)
from media_manager.tv.metadata import TvMetadataService
from media_manager.tv.repository import TvRepository
from media_manager.tv.schemas import EpisodeFile, Show

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
            indexer_service=None,  # type: ignore[arg-type]
            notification_service=notification_service,
        )
        self.tv_repository = tv_repository
        self.tv_metadata_service = tv_metadata_service

    def get_media_root_path(self, media: Show) -> Path:
        misc_config = MediaManagerConfig().misc
        return self.get_root_directory(
            media=media,
            default_dir=misc_config.tv_directory,
            libraries=misc_config.tv_libraries,
        )

    def import_tv_show(
        self,
        show: Show,
        source_directory: Path,
        quality: Quality = Quality.unknown,
        torrent_id: str | None = None,
        file_path_suffix: str = "",
    ) -> bool:
        video_files, _, _ = get_files_for_import(directory=source_directory)
        if not video_files:
            return False

        any_imported = False
        for video_file in video_files:
            # Simple heuristic for season/episode from filename
            match = re.search(r"S(\d+)E(\d+)", video_file.name, re.IGNORECASE)
            if match:
                s_num, e_num = int(match.group(1)), int(match.group(2))
                season_dir = self.get_media_root_path(show) / f"Season {s_num}"
                season_dir.mkdir(parents=True, exist_ok=True)

                target_name = (
                    f"{remove_special_characters(show.name)} - S{s_num:02d}E{e_num:02d}"
                )
                if file_path_suffix:
                    target_name += f" - {file_path_suffix}"
                target_file = season_dir / f"{target_name}{video_file.suffix}"

                import_file(target_file=target_file, source_file=video_file)
                any_imported = True

                # Update DB
                try:
                    season = self.tv_repository.get_season_by_number(s_num, show.id)
                    episode = next(
                        (e for e in season.episodes if e.number == e_num), None
                    )
                    if episode:
                        self.tv_repository.add_episode_file(
                            EpisodeFile(
                                episode_id=episode.id,
                                quality=quality,
                                torrent_id=torrent_id,
                                file_path_suffix=file_path_suffix,
                            )
                        )
                except Exception:
                    log.exception(f"Could not update DB for {video_file.name}")
        return any_imported

    def import_torrent_files(self, torrent: Torrent, show: Show) -> None:
        success = self.import_tv_show(
            show=show,
            source_directory=get_torrent_filepath(torrent),
            quality=torrent.quality,
            torrent_id=torrent.id,
        )
        if success:
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)
            self.notify_import_success(show.name, "TV show")
        else:
            self.notify_import_failure(show.name, "TV show")

    def get_import_candidates(
        self, tv_path: Path, metadata_provider: AbstractMetadataProvider
    ) -> MediaImportSuggestion:
        return super().get_import_candidates(
            directory=tv_path,
            metadata_provider=metadata_provider,
            search_func=self.tv_metadata_service.search_for_show,
        )

    def import_existing_tv_show(self, tv_show: Show, source_directory: Path) -> bool:
        def _logic(s: Show, path: Path, _: Callable[[Any], Any]) -> bool:
            return self.import_tv_show(s, path, file_path_suffix="IMPORTED")

        return self.import_existing_media(
            media=tv_show,
            source_directory=source_directory,
            import_func=_logic,
            add_file_record_func=lambda _: (
                None
            ),  # Handled inside import_tv_show for now
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
            import_torrent_func=self.import_torrent_files,
            media_type_name="tv show",
        )
