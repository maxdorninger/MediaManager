import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from media_manager.common.repository import BaseRepository
from media_manager.exceptions import InvalidConfigError, NotFoundError
from media_manager.indexer.service import IndexerService
from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.notification.service import NotificationService
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import (
    get_importable_media_directories,
    remove_special_characters,
)

log = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")


class BaseMediaService[T, S]:
    """
    Base service providing common logic for media modules.
    """

    def __init__(
        self,
        repository: BaseRepository[T, S],
        torrent_service: TorrentService,
        indexer_service: IndexerService,
        notification_service: NotificationService,
    ) -> None:
        self.repository = repository
        self.torrent_service = torrent_service
        self.indexer_service = indexer_service
        self.notification_service = notification_service

    def get_all_media(self) -> list[S]:
        return self.repository.get_all()

    def get_root_directory(
        self, media: S, default_dir: Path, libraries: list[Any]
    ) -> Path:
        """
        Determines the root directory for a media item.
        """
        if hasattr(media, "library") and media.library:
            for library in libraries:
                if library.name == media.library:
                    return Path(library.path) / Path(
                        remove_special_characters(media.name)
                    )
        return default_dir / Path(remove_special_characters(media.name))

    def get_media_root_path(self, media: S) -> Path:
        """
        To be implemented by subclasses if they have specific directory logic.
        """
        raise NotImplementedError

    def notify_import_success(self, media_name: str, media_type: str) -> None:
        if self.notification_service:
            self.notification_service.send_notification_to_all_providers(
                title=f"{media_type.capitalize()} Downloaded",
                message=f"{media_type.capitalize()} {media_name} has been successfully downloaded and imported.",
            )

    def notify_import_failure(
        self, media_name: str, media_type: str, error_msg: str = ""
    ) -> None:
        if self.notification_service:
            msg = f"Failed to import files for {media_type} {media_name}."
            if error_msg:
                msg += f" Error: {error_msg}"
            self.notification_service.send_notification_to_all_providers(
                title="Import Failed",
                message=msg,
            )

    def get_import_candidates(
        self,
        directory: Path,
        metadata_provider: AbstractMetadataProvider,
        search_func: Callable[
            [str, AbstractMetadataProvider], list[MetaDataProviderSearchResult]
        ],
    ) -> MediaImportSuggestion:
        # Implementation from previous turn
        name, _ = self._extract_name_and_year(directory.name)
        candidates = search_func(name, metadata_provider)
        return MediaImportSuggestion(
            directory=str(directory),
            candidates=candidates,
        )

    def _extract_name_and_year(self, directory_name: str) -> tuple[str, int | None]:
        import re

        match = re.search(r"^(.*)\s\((\d{4})\)$", directory_name)
        if match:
            return match.group(1), int(match.group(2))
        return directory_name, None

    def get_importable_media(
        self,
        root_path: Path,
        metadata_provider: AbstractMetadataProvider,
        get_candidates_func: Callable[
            [Path, AbstractMetadataProvider], MediaImportSuggestion
        ],
    ) -> list[MediaImportSuggestion]:
        importable_dirs = get_importable_media_directories(root_path)
        return [
            get_candidates_func(directory, metadata_provider)
            for directory in importable_dirs
        ]

    def import_existing_media(
        self,
        media: S,
        source_directory: Path,
        import_func: Callable[[S, Path, Callable[[Any], None]], bool],
        add_file_record_func: Callable[[Any], Any],
    ) -> bool:
        success = import_func(media, source_directory, add_file_record_func)
        if success:
            log.info(f"Successfully imported {media.name} from {source_directory}")
        return success

    def import_all_torrents_base(
        self,
        get_media_func: Callable[[Any], S],
        import_torrent_func: Callable[[Any, S], None],
        media_type_name: str,
    ) -> None:
        log.info(f"Importing all torrents for {media_type_name}")
        torrents = self.torrent_service.get_completed_torrents()
        for t in torrents:
            if t.imported:
                continue
            try:
                media = get_media_func(t)
                if media:
                    import_torrent_func(t, media)
            except Exception:
                log.exception(f"Error importing torrent {t.title}")
        log.info(f"Finished importing all torrents for {media_type_name}")


class BaseMetadataService[T, S]:
    """
    Base service for metadata operations.
    """

    def __init__(self, repository: BaseRepository[T, S]) -> None:
        self.repository = repository

    def check_if_exists(self, external_id: int, metadata_provider: str) -> bool:
        try:
            self.repository.get_by_external_id(
                external_id=external_id, metadata_provider=metadata_provider
            )
        except NotFoundError:
            return False
        else:
            return True

    def add_media_base(
        self,
        external_id: int,
        metadata_provider: AbstractMetadataProvider,  # noqa: ARG002
        get_metadata_func: Callable[..., S],
        save_func: Callable[[S], S],
        download_poster_func: Callable[[S], bool],
        language: str | None = None,
    ) -> S:
        media_with_metadata = get_metadata_func(external_id, language=language)
        if not media_with_metadata:
            raise NotFoundError

        saved_media = save_func(media_with_metadata)
        download_poster_func(saved_media)
        return saved_media

    def search_for_media_base(
        self,
        query: str,
        metadata_provider: AbstractMetadataProvider,
        search_func: Callable[[str | None], list[MetaDataProviderSearchResult]],
        get_by_external_id_func: Callable[..., S],
    ) -> list[MetaDataProviderSearchResult]:
        results = search_func(query)
        for result in results:
            if self.check_if_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            ):
                result.added = True
                try:
                    media = get_by_external_id_func(
                        external_id=result.external_id,
                        metadata_provider=metadata_provider.name,
                    )
                    result.id = media.id
                except Exception:
                    log.exception(
                        f"Unable to find internal ID for {result.external_id} on {metadata_provider.name}"
                    )
        return results

    def get_popular_media_base(
        self,
        metadata_provider: AbstractMetadataProvider,
        search_func: Callable[[str | None], list[MetaDataProviderSearchResult]],
    ) -> list[MetaDataProviderSearchResult]:
        results = search_func(None)
        return [
            result
            for result in results
            if not self.check_if_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            )
        ]

    def update_all_metadata_base(
        self,
        get_all_to_update_func: Callable[[], list[S]],
        update_single_func: Callable[[S, AbstractMetadataProvider], S | None],
        tmdb_provider_class: Callable[[], AbstractMetadataProvider],
        tvdb_provider_class: Callable[[], AbstractMetadataProvider],
        media_type_name: str,
    ) -> None:
        log.info(f"Updating metadata for all {media_type_name}")
        media_list = get_all_to_update_func()
        log.info(f"Found {len(media_list)} {media_type_name} to update")
        for item in media_list:
            try:
                if item.metadata_provider == "tmdb":
                    provider = tmdb_provider_class()
                elif item.metadata_provider == "tvdb":
                    provider = tvdb_provider_class()
                else:
                    log.error(
                        f"Unsupported provider {item.metadata_provider} for {item.name}"
                    )
                    continue
                update_single_func(item, provider)
            except InvalidConfigError:
                log.exception(f"Config error for {item.name}")
            except Exception:
                log.exception(f"Error updating {item.name}")
