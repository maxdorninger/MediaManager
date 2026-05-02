import logging
from pathlib import Path
from typing import Generic, TypeVar, List, Any, Optional, Callable

from media_manager.common.repository import BaseRepository
from media_manager.exceptions import NotFoundError, RenameError
from media_manager.metadataProvider.abstract_metadata_provider import AbstractMetadataProvider
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.service import TorrentService
from media_manager.indexer.service import IndexerService
from media_manager.notification.service import NotificationService
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.torrent.utils import (
    remove_special_characters,
    get_importable_media_directories,
    extract_external_id_from_string,
    remove_special_chars_and_parentheses,
)

log = logging.getLogger(__name__)

T = TypeVar("T")
S = TypeVar("S")

class BaseMediaService(Generic[T, S]):
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

    def get_all(self) -> List[S]:
        return self.repository.get_all()

    def check_if_exists(
        self, *, external_id: Optional[int] = None, metadata_provider: Optional[str] = None, media_id: Optional[Any] = None
    ) -> bool:
        if external_id is not None and metadata_provider is not None:
            try:
                self.repository.get_by_external_id(
                    external_id=external_id, metadata_provider=metadata_provider
                )
                return True
            except NotFoundError:
                return False
        elif media_id is not None:
            try:
                self.repository.get_by_id(id=media_id)
                return True
            except NotFoundError:
                return False
        return False

    def get_root_directory(self, media: S, default_dir: Path, libraries: List[Any]) -> Path:
        """
        Common logic for determining the root directory of a media item.
        """
        directory_name = f"{remove_special_characters(media.name)} ({media.year}) [{media.metadata_provider}id-{media.external_id}]"
        
        if media.library != "Default":
            for library in libraries:
                if library.name == media.library:
                    return Path(library.path) / directory_name
        
        return default_dir / directory_name

    def get_import_candidates(
        self, directory: Path, metadata_provider: AbstractMetadataProvider, search_func: Callable[[str, AbstractMetadataProvider], List[Any]]
    ) -> MediaImportSuggestion:
        """
        Scans a directory and searches for metadata candidates.
        """
        query = remove_special_chars_and_parentheses(directory.name)
        search_result = search_func(query, metadata_provider)
        import_candidates = MediaImportSuggestion(
            directory=directory,
            candidates=search_result,
        )
        log.debug(
            f"Found {len(search_result)} candidates for {directory.name} in {directory.parent}"
        )
        return import_candidates

    def get_importable_media(
        self, root_path: Path, metadata_provider: AbstractMetadataProvider, get_candidates_func: Callable[[Path, AbstractMetadataProvider], MediaImportSuggestion]
    ) -> List[MediaImportSuggestion]:
        """
        Scans the root path for media items that are not yet in the database.
        """
        importable_media: List[MediaImportSuggestion] = []
        candidate_dirs = get_importable_media_directories(root_path)

        for media_dir in candidate_dirs:
            metadata, external_id = extract_external_id_from_string(media_dir.name)
            if metadata is not None and external_id is not None:
                if self.check_if_exists(external_id=external_id, metadata_provider=metadata):
                    log.debug(f"Media {media_dir.name} already exists in the database, skipping.")
                    continue
                else:
                    log.debug(f"Media {media_dir.name} not found in database, checking for import candidates.")

            import_candidates = get_candidates_func(media_dir, metadata_provider)
            importable_media.append(import_candidates)

        log.debug(f"Found {len(importable_media)} importable media items.")
        return importable_media

    def import_existing_media(
        self, media: S, source_directory: Path, import_func: Callable[..., Any], add_file_record_func: Callable[[Any], None]
    ) -> bool:
        """
        Imports existing media by renaming it and calling module-specific import logic.
        """
        new_source_path = source_directory.parent / ("." + source_directory.name)
        try:
            source_directory.rename(new_source_path)
        except Exception as e:
            log.exception(f"Failed to rename {source_directory} to {new_source_path}")
            raise RenameError from e

        # The actual import logic (e.g. scanning for files and creating DB records) is handled by the callback
        return import_func(media, new_source_path, add_file_record_func)

    def import_all_torrents_base(self, get_media_func: Callable[[Any], Optional[S]], import_torrent_func: Callable[[Any, S], None], media_type_name: str) -> None:
        """
        Generic method to import all finished torrents for a specific media type.
        """
        log.info(f"Importing all torrents for {media_type_name}")
        torrents = self.torrent_service.get_all_torrents()
        log.info(f"Found {len(torrents)} torrents to import")
        for t in torrents:
            try:
                # We only want to import torrents that haven't been imported yet and are finished
                # TorrentStatus is imported from torrent.schemas
                from media_manager.torrent.schemas import TorrentStatus
                if not t.imported and t.status == TorrentStatus.finished:
                    media = get_media_func(t)
                    if media is None:
                        # This torrent might belong to another media type, so we skip it without error
                        log.debug(f"Torrent {t.title} is not a {media_type_name} torrent, skipping.")
                        continue
                    
                    import_torrent_func(t, media)
            except Exception as e:
                log.error(f"Error importing torrent {t.title}: {e}", exc_info=True)
        log.info(f"Finished importing all torrents for {media_type_name}")


class BaseMetadataService(Generic[T, S]):
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
            return True
        except NotFoundError:
            return False

    def add_media_base(
        self,
        external_id: int,
        metadata_provider: AbstractMetadataProvider,
        get_metadata_func: Callable[..., S],
        save_func: Callable[[S], S],
        download_poster_func: Callable[[S], bool],
        language: Optional[str] = None,
    ) -> S:
        media_with_metadata = get_metadata_func(external_id=external_id, language=language)
        if not media_with_metadata:
            raise NotFoundError
        
        saved_media = save_func(media_with_metadata)
        download_poster_func(saved_media)
        return saved_media

    def search_for_media_base(
        self,
        query: str,
        metadata_provider: AbstractMetadataProvider,
        search_func: Callable[[Optional[str]], List[MetaDataProviderSearchResult]],
        get_by_external_id_func: Callable[..., S],
    ) -> List[MetaDataProviderSearchResult]:
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
                    log.error(
                        f"Unable to find internal ID for {result.external_id} on {metadata_provider.name}"
                    )
        return results

    def get_popular_media_base(
        self,
        metadata_provider: AbstractMetadataProvider,
        search_func: Callable[[Optional[str]], List[MetaDataProviderSearchResult]],
    ) -> List[MetaDataProviderSearchResult]:
        results = search_func(None)
        return [
            result
            for result in results
            if not self.check_if_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            )
        ]
