import logging
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
from media_manager.movies.metadata import MovieMetadataService
from media_manager.movies.repository import MovieRepository
from media_manager.movies.schemas import Movie, MovieFile

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
            indexer_service=None,  # type: ignore
            notification_service=notification_service,
        )
        self.movie_repository = movie_repository
        self.movie_metadata_service = movie_metadata_service

    def get_movie_root_path(self, movie: Movie) -> Path:
        misc_config = MediaManagerConfig().misc
        return self.get_root_directory(
            media=movie,
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
        movie_file_name = f"{remove_special_characters(movie.name)} ({movie.year})"
        movie_root_path = self.get_movie_root_path(movie=movie)
        success: bool = False
        if file_path_suffix != "":
            movie_file_name += f" - {file_path_suffix}"

        try:
            movie_root_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            log.exception(f"Failed to create directory {movie_root_path}")
            return False

        # import movie video
        if video_files:
            target_video_file = (
                movie_root_path / f"{movie_file_name}{video_files[0].suffix}"
            )
            import_file(target_file=target_video_file, source_file=video_files[0])
            success = True

        # import subtitles
        for subtitle_file in subtitle_files:
            language_code_match = re.search(
                r"[. ]([a-z]{2})\.srt$", subtitle_file.name, re.IGNORECASE
            )
            if not language_code_match:
                log.warning(
                    f"Subtitle file {subtitle_file.name} does not match expected format, can't extract language code, skipping."
                )
                continue
            language_code = language_code_match.group(1)
            target_subtitle_file = (
                movie_root_path / f"{movie_file_name}.{language_code}.srt"
            )
            import_file(target_file=target_subtitle_file, source_file=subtitle_file)

        return success

    def import_torrent_files(self, torrent: Torrent, movie: Movie) -> None:
        """
        Organizes files from a torrent into the movie directory structure.
        :param torrent: The Torrent object
        :param movie: The Movie object
        """

        video_files, subtitle_files, _all_files = get_files_for_import(torrent=torrent)

        if len(video_files) != 1:
            # Send notification about multiple video files found
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Manual Import Required",
                    message=f"Multiple video files found for movie {movie.name}. Please import manually.",
                )
            log.error(
                f"Found {len(video_files)} video files for movie {movie.name}, expected 1. Skipping auto import."
            )
            return

        log.debug(
            f"Importing these {len(video_files)} video files and {len(subtitle_files)} subtitle files"
        )

        movie_files: list[MovieFile] = self.torrent_service.get_movie_files_of_torrent(
            torrent=torrent
        )
        log.info(
            f"Found {len(movie_files)} movie files associated with torrent {torrent.title}"
        )

        success = [
            self.import_movie(
                movie, video_files, subtitle_files, movie_file.file_path_suffix
            )
            for movie_file in movie_files
        ]

        if all(success):
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)

            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Movie Downloaded",
                    message=f"Movie {movie.name} has been successfully downloaded and imported.",
                )
        else:
            log.error(
                f"Failed to import files for torrent {torrent.title}. Check logs for details."
            )

            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Import Failed",
                    message=f"Failed to import files for movie {movie.name}. Please check logs.",
                )

        log.info(f"Finished importing files for torrent {torrent.title}")

    def get_import_candidates(
        self, movie: Path, metadata_provider: AbstractMetadataProvider
    ) -> MediaImportSuggestion:
        return super().get_import_candidates(
            directory=movie,
            metadata_provider=metadata_provider,
            search_func=self.movie_metadata_service.search_for_movie,
        )

    def import_existing_movie(self, movie: Movie, source_directory: Path) -> bool:
        def _import_logic(m: Movie, path: Path, add_record_cb: Callable[[MovieFile], None]) -> bool:
            video_files, subtitle_files, _all_files = get_files_for_import(directory=path)
            success = self.import_movie(
                movie=m,
                video_files=video_files,
                subtitle_files=subtitle_files,
                file_path_suffix="IMPORTED",
            )
            if success:
                add_record_cb(
                    MovieFile(
                        movie_id=m.id,
                        file_path_suffix="IMPORTED",
                        torrent_id=None,
                        quality=Quality.unknown,
                    )
                )
            return success

        return self.import_existing_media(
            media=movie,
            source_directory=source_directory,
            import_func=_import_logic,
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
