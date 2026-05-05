import logging
import re
from collections.abc import Callable
from pathlib import Path

from media_manager.common.service import BaseMediaService
from media_manager.config import MediaManagerConfig
from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.movies.metadata import MovieMetadataService
from media_manager.movies.repository import MovieRepository
from media_manager.movies.schemas import Movie, MovieFile
from media_manager.notification.service import NotificationService
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.schemas import Quality, Torrent
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import (
    get_files_for_import,
    import_file,
    remove_special_characters,
)

log = logging.getLogger(__name__)


class MovieImportService(BaseMediaService[Movie, Movie]):
    def __init__(
        self,
        movie_repository: MovieRepository,
        torrent_service: TorrentService,
        notification_service: NotificationService,
        movie_metadata_service: MovieMetadataService,
    ) -> None:
        super().__init__(
            repository=movie_repository,
            torrent_service=torrent_service,
            indexer_service=None,  # type: ignore[arg-type]
            notification_service=notification_service,
        )
        self.movie_repository = movie_repository
        self.movie_metadata_service = movie_metadata_service

    def get_media_root_path(self, media: Movie) -> Path:
        misc_config = MediaManagerConfig().misc
        return self.get_root_directory(
            media=media,
            default_dir=misc_config.movie_directory,
            libraries=misc_config.movie_libraries,
        )

    def import_movie(
        self,
        movie: Movie,
        video_files: list[Path],
        subtitle_files: list[Path],
        file_path_suffix: str = "",
    ) -> bool:
        if not video_files and not subtitle_files:
            log.error(f"No video or subtitle files found for movie {movie.name}")
            return False

        movie_file_name = f"{remove_special_characters(movie.name)} ({movie.year})"
        movie_root_path = self.get_media_root_path(media=movie)
        if file_path_suffix:
            movie_file_name += f" - {file_path_suffix}"

        imported_any = False
        try:
            movie_root_path.mkdir(parents=True, exist_ok=True)
            if video_files:
                target_video_file = (
                    movie_root_path / f"{movie_file_name}{video_files[0].suffix}"
                )
                import_file(target_file=target_video_file, source_file=video_files[0])
                imported_any = True

            for subtitle_file in subtitle_files:
                match = re.search(
                    r"[. ]([a-z]{2})\.srt$", subtitle_file.name, re.IGNORECASE
                )
                if match:
                    lang = match.group(1)
                    target = movie_root_path / f"{movie_file_name}.{lang}.srt"
                    import_file(target_file=target, source_file=subtitle_file)
                    imported_any = True
        except Exception:
            log.exception(f"Failed to import movie {movie.name}")
            return False
        else:
            return imported_any

    def import_torrent_files(self, torrent: Torrent, movie: Movie) -> None:
        video_files, subtitle_files, _ = get_files_for_import(torrent=torrent)
        if len(video_files) != 1:
            self.notify_import_failure(
                movie.name,
                "movie",
                "Multiple video files found. Manual import required.",
            )
            return

        movie_files = self.torrent_service.get_movie_files_of_torrent(torrent=torrent)
        if not movie_files:
            torrent.imported = False
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)
            self.notify_import_failure(movie.name, "movie")
            return

        success = [
            self.import_movie(movie, video_files, subtitle_files, mf.file_path_suffix)
            for mf in movie_files
        ]

        if all(success):
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)
            self.notify_import_success(movie.name, "movie")
        else:
            self.notify_import_failure(movie.name, "movie")

    def get_import_candidates(
        self, movie_path: Path, metadata_provider: AbstractMetadataProvider
    ) -> MediaImportSuggestion:
        return super().get_import_candidates(
            directory=movie_path,
            metadata_provider=metadata_provider,
            search_func=self.movie_metadata_service.search_for_movie,
        )

    def import_existing_movie(self, movie: Movie, source_directory: Path) -> bool:
        def _logic(m: Movie, path: Path, add_cb: Callable[[MovieFile], None]) -> bool:
            v, s, _ = get_files_for_import(directory=path)
            res = self.import_movie(m, v, s, "IMPORTED")
            if res:
                add_cb(
                    MovieFile(
                        movie_id=m.id,
                        file_path_suffix="IMPORTED",
                        torrent_id=None,
                        quality=Quality.unknown,
                    )
                )
            return res

        return self.import_existing_media(
            media=movie,
            source_directory=source_directory,
            import_func=_logic,
            add_file_record_func=self.movie_repository.add_movie_file,
        )

    def get_importable_movies(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MediaImportSuggestion]:
        return self.get_importable_media(
            root_path=MediaManagerConfig().misc.movie_directory,
            metadata_provider=metadata_provider,
            get_candidates_func=self.get_import_candidates,
        )

    def import_all_torrents(self) -> None:
        self.import_all_torrents_base(
            get_media_func=self.torrent_service.get_movie_of_torrent,
            import_torrent_func=self.import_torrent_files,
            media_type_name="movie",
        )
