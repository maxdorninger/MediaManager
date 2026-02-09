import mimetypes
import shutil
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from media_manager.books import log
from media_manager.books.repository import BookRepository
from media_manager.books.schemas import (
    Author,
    AuthorId,
    BookFile,
    BookId,
    BookRequest,
    BookRequestId,
    PublicAuthor,
    PublicBookFile,
    RichAuthorTorrent,
    RichBookRequest,
)
from media_manager.config import MediaManagerConfig
from media_manager.database import SessionLocal, get_session
from media_manager.exceptions import NotFoundError
from media_manager.indexer.repository import IndexerRepository
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.indexer.service import IndexerService
from media_manager.metadataProvider.abstract_book_metadata_provider import (
    AbstractBookMetadataProvider,
)
from media_manager.metadataProvider.openlibrary import OpenLibraryMetadataProvider
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.notification.repository import NotificationRepository
from media_manager.notification.service import NotificationService
from media_manager.torrent.repository import TorrentRepository
from media_manager.torrent.schemas import (
    QualityStrings,
    Torrent,
    TorrentStatus,
)
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import (
    import_file,
    list_files_recursively,
    remove_special_characters,
)

BOOK_EXTENSIONS = {
    ".epub", ".mobi", ".pdf", ".azw3", ".fb2", ".cbz", ".cbr",
    ".m4b", ".mp3", ".m4a", ".ogg", ".flac",
}


class BookService:
    def __init__(
        self,
        book_repository: BookRepository,
        torrent_service: TorrentService,
        indexer_service: IndexerService,
        notification_service: NotificationService,
    ) -> None:
        self.book_repository = book_repository
        self.torrent_service = torrent_service
        self.indexer_service = indexer_service
        self.notification_service = notification_service

    def add_author(
        self,
        external_id: str,
        metadata_provider: AbstractBookMetadataProvider,
    ) -> Author:
        author_with_metadata = metadata_provider.get_author_metadata(
            author_id=external_id
        )
        if not author_with_metadata:
            raise NotFoundError

        saved_author = self.book_repository.save_author(author=author_with_metadata)
        metadata_provider.download_author_cover_image(author=saved_author)
        return saved_author

    def add_book_request(self, book_request: BookRequest) -> BookRequest:
        return self.book_repository.add_book_request(book_request=book_request)

    def get_book_request_by_id(
        self, book_request_id: BookRequestId
    ) -> BookRequest:
        return self.book_repository.get_book_request(
            book_request_id=book_request_id
        )

    def update_book_request(self, book_request: BookRequest) -> BookRequest:
        self.book_repository.delete_book_request(
            book_request_id=book_request.id
        )
        return self.book_repository.add_book_request(book_request=book_request)

    def delete_book_request(self, book_request_id: BookRequestId) -> None:
        self.book_repository.delete_book_request(
            book_request_id=book_request_id
        )

    def delete_author(
        self,
        author: Author,
        delete_files_on_disk: bool = False,
        delete_torrents: bool = False,
    ) -> None:
        if delete_files_on_disk or delete_torrents:
            if delete_files_on_disk:
                author_dir = self.get_author_root_path(author=author)
                if author_dir.exists() and author_dir.is_dir():
                    try:
                        shutil.rmtree(author_dir)
                        log.info(f"Deleted author directory: {author_dir}")
                    except OSError:
                        log.exception(f"Deleting author directory: {author_dir}")

            if delete_torrents:
                author_torrents = self.book_repository.get_torrents_by_author_id(
                    author_id=author.id
                )
                for book_torrent in author_torrents:
                    torrent = self.torrent_service.get_torrent_by_id(
                        torrent_id=book_torrent.torrent_id
                    )
                    try:
                        self.torrent_service.cancel_download(
                            torrent=torrent, delete_files=True
                        )
                        log.info(f"Deleted torrent: {torrent.title}")
                    except Exception:
                        log.warning(
                            f"Failed to delete torrent {torrent.hash}",
                            exc_info=True,
                        )

        self.book_repository.delete_author(author_id=author.id)

    def get_public_book_files(
        self, book_id: BookId
    ) -> list[PublicBookFile]:
        book_files = self.book_repository.get_book_files_by_book_id(
            book_id=book_id
        )
        public_book_files = [PublicBookFile.model_validate(x) for x in book_files]
        result = []
        for book_file in public_book_files:
            book_file.downloaded = self.book_file_exists_on_disk(
                book_file=book_file
            )
            result.append(book_file)
        return result

    def book_file_exists_on_disk(self, book_file: BookFile) -> bool:
        if book_file.torrent_id is None:
            return True
        torrent_file = self.torrent_service.get_torrent_by_id(
            torrent_id=book_file.torrent_id
        )
        return torrent_file.imported

    def get_all_authors(self) -> list[Author]:
        return self.book_repository.get_authors()

    def get_popular_authors(
        self, metadata_provider: AbstractBookMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        results = metadata_provider.search_author()
        return [
            result
            for result in results
            if not self._check_if_author_exists(
                external_id=str(result.external_id),
                metadata_provider=metadata_provider.name,
            )
        ]

    def _check_if_author_exists(
        self, external_id: str, metadata_provider: str
    ) -> bool:
        try:
            self.book_repository.get_author_by_external_id(
                external_id=external_id, metadata_provider=metadata_provider
            )
            return True
        except NotFoundError:
            return False

    def search_for_author(
        self, query: str, metadata_provider: AbstractBookMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        results = metadata_provider.search_author(query)
        for result in results:
            try:
                author = self.book_repository.get_author_by_external_id(
                    external_id=str(result.external_id),
                    metadata_provider=metadata_provider.name,
                )
                result.added = True
                result.id = author.id
            except NotFoundError:
                pass
            except Exception:
                log.error(
                    f"Unable to find internal author ID for {result.external_id} on {metadata_provider.name}"
                )
        return results

    def get_public_author_by_id(self, author: Author) -> PublicAuthor:
        public_author = PublicAuthor.model_validate(author)
        for book in public_author.books:
            book_files = self.book_repository.get_book_files_by_book_id(
                book_id=book.id
            )
            book.downloaded = len(book_files) > 0
        return public_author

    def get_author_by_id(self, author_id: AuthorId) -> Author:
        return self.book_repository.get_author_by_id(author_id=author_id)

    def get_author_by_external_id(
        self, external_id: str, metadata_provider: str
    ) -> Author | None:
        return self.book_repository.get_author_by_external_id(
            external_id=external_id, metadata_provider=metadata_provider
        )

    def get_all_book_requests(self) -> list[RichBookRequest]:
        return self.book_repository.get_book_requests()

    def set_author_library(self, author: Author, library: str) -> None:
        self.book_repository.set_author_library(
            author_id=author.id, library=library
        )

    def get_torrents_for_author(self, author: Author) -> RichAuthorTorrent:
        author_torrents = self.book_repository.get_torrents_by_author_id(
            author_id=author.id
        )
        return RichAuthorTorrent(
            author_id=author.id,
            name=author.name,
            metadata_provider=author.metadata_provider,
            torrents=author_torrents,
        )

    def get_all_authors_with_torrents(self) -> list[RichAuthorTorrent]:
        authors = self.book_repository.get_all_authors_with_torrents()
        return [self.get_torrents_for_author(author=author) for author in authors]

    def get_all_available_torrents_for_book(
        self,
        author: Author,
        book_name: str,
        search_query_override: str | None = None,
    ) -> list[IndexerQueryResult]:
        return self.indexer_service.search_book(
            author=author,
            book_name=book_name,
            search_query_override=search_query_override,
        )

    def download_torrent(
        self,
        public_indexer_result_id: IndexerQueryResultId,
        author: Author,
        book_id: BookId,
        override_file_path_suffix: str = "",
    ) -> Torrent:
        indexer_result = self.indexer_service.get_result(
            result_id=public_indexer_result_id
        )
        book_torrent = self.torrent_service.download(indexer_result=indexer_result)
        self.torrent_service.pause_download(torrent=book_torrent)
        book_file = BookFile(
            book_id=book_id,
            quality=indexer_result.quality,
            torrent_id=book_torrent.id,
            file_path_suffix=override_file_path_suffix,
        )
        try:
            self.book_repository.add_book_file(book_file=book_file)
        except IntegrityError:
            log.warning(
                f"Book file for author {author.name} and torrent {book_torrent.title} already exists"
            )
            self.torrent_service.cancel_download(
                torrent=book_torrent, delete_files=True
            )
            raise
        else:
            log.info(
                f"Added book file for author {author.name} and torrent {book_torrent.title}"
            )
            self.torrent_service.resume_download(torrent=book_torrent)
        return book_torrent

    def download_approved_book_request(
        self, book_request: BookRequest, author: Author, book_name: str
    ) -> bool:
        if not book_request.authorized:
            msg = "Book request is not authorized"
            raise ValueError(msg)

        log.info(f"Downloading approved book request {book_request.id}")

        torrents = self.get_all_available_torrents_for_book(
            author=author, book_name=book_name
        )
        available_torrents: list[IndexerQueryResult] = []

        for torrent in torrents:
            if torrent.seeders < 3:
                log.debug(
                    f"Skipping torrent {torrent.title} for book request {book_request.id}, too few seeders"
                )
            else:
                available_torrents.append(torrent)

        if len(available_torrents) == 0:
            log.warning(
                f"No torrents found for book request {book_request.id}"
            )
            return False

        available_torrents.sort()

        torrent = self.torrent_service.download(indexer_result=available_torrents[0])
        book_file = BookFile(
            book_id=book_request.book_id,
            quality=torrent.quality,
            torrent_id=torrent.id,
            file_path_suffix=QualityStrings[torrent.quality.name].value.upper(),
        )
        try:
            self.book_repository.add_book_file(book_file=book_file)
        except IntegrityError:
            log.warning(
                f"Book file for torrent {torrent.title} already exists"
            )
        self.delete_book_request(book_request.id)
        return True

    def get_author_root_path(self, author: Author) -> Path:
        misc_config = MediaManagerConfig().misc
        author_dir_name = remove_special_characters(author.name)
        author_file_path = misc_config.books_directory / author_dir_name

        if author.library != "Default":
            for library in misc_config.books_libraries:
                if library.name == author.library:
                    log.debug(
                        f"Using library {library.name} for author {author.name}"
                    )
                    return Path(library.path) / author_dir_name
            log.warning(
                f"Library {author.library} not found in config, using default library"
            )
        return author_file_path

    def import_book_files(self, torrent: Torrent, author: Author) -> None:
        from media_manager.torrent.utils import get_torrent_filepath

        torrent_path = get_torrent_filepath(torrent=torrent)
        all_files = list_files_recursively(path=torrent_path)

        book_files = [
            f
            for f in all_files
            if f.suffix.lower() in BOOK_EXTENSIONS
            or (mimetypes.guess_type(str(f))[0] or "").startswith("application/epub")
        ]

        if not book_files:
            log.warning(
                f"No book files found in torrent {torrent.title} for author {author.name}"
            )
            return

        log.info(
            f"Found {len(book_files)} book files for import from torrent {torrent.title}"
        )

        author_root = self.get_author_root_path(author=author)
        book_dir = author_root / remove_special_characters(torrent.title)

        try:
            book_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            log.exception(f"Failed to create directory {book_dir}")
            return

        success = True
        for book_file in book_files:
            target_file = book_dir / book_file.name
            try:
                import_file(target_file=target_file, source_file=book_file)
            except Exception:
                log.exception(f"Failed to import book file {book_file}")
                success = False

        if success:
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)

            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Book Downloaded",
                    message=f"Book for {author.name} has been successfully downloaded and imported.",
                )
        else:
            log.error(
                f"Failed to import some files for torrent {torrent.title}."
            )
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Import Failed",
                    message=f"Failed to import some book files for {author.name}. Please check logs.",
                )

    def update_author_metadata(
        self,
        db_author: Author,
        metadata_provider: AbstractBookMetadataProvider,
    ) -> Author | None:
        log.debug(f"Found author: {db_author.name} for metadata update.")

        fresh_author_data = metadata_provider.get_author_metadata(
            author_id=db_author.external_id
        )
        if not fresh_author_data:
            log.warning(
                f"Could not fetch fresh metadata for author: {db_author.name} (ID: {db_author.external_id})"
            )
            return None

        self.book_repository.update_author_attributes(
            author_id=db_author.id,
            name=fresh_author_data.name,
            overview=fresh_author_data.overview,
        )

        updated_author = self.book_repository.get_author_by_id(
            author_id=db_author.id
        )
        log.info(f"Successfully updated metadata for author ID: {db_author.id}")
        metadata_provider.download_author_cover_image(author=updated_author)
        return updated_author


def auto_download_all_approved_book_requests() -> None:
    db: Session = SessionLocal() if SessionLocal else next(get_session())
    book_repository = BookRepository(db=db)
    torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
    indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
    notification_service = NotificationService(
        notification_repository=NotificationRepository(db=db)
    )
    book_service = BookService(
        book_repository=book_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
        notification_service=notification_service,
    )

    log.info("Auto downloading all approved book requests")
    book_requests = book_repository.get_book_requests()
    log.info(f"Found {len(book_requests)} book requests to process")
    count = 0

    for book_request in book_requests:
        if book_request.authorized:
            book = book_repository.get_book(book_id=book_request.book_id)
            author = book_repository.get_author_by_id(
                author_id=AuthorId(book_request.author.id)
            )
            if book_service.download_approved_book_request(
                book_request=book_request,
                author=author,
                book_name=book.name,
            ):
                count += 1
            else:
                log.info(
                    f"Could not download book request {book_request.id}"
                )

    log.info(f"Auto downloaded {count} approved book requests")
    db.commit()
    db.close()


def import_all_book_torrents() -> None:
    with next(get_session()) as db:
        book_repository = BookRepository(db=db)
        torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
        indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
        notification_service = NotificationService(
            notification_repository=NotificationRepository(db=db)
        )
        book_service = BookService(
            book_repository=book_repository,
            torrent_service=torrent_service,
            indexer_service=indexer_service,
            notification_service=notification_service,
        )
        log.info("Importing all book torrents")
        torrents = torrent_service.get_all_torrents()
        for t in torrents:
            try:
                if not t.imported and t.status == TorrentStatus.finished:
                    author = book_repository.get_author_by_torrent_id(
                        torrent_id=t.id
                    )
                    if author is None:
                        continue
                    book_service.import_book_files(torrent=t, author=author)
            except RuntimeError:
                log.exception(f"Failed to import torrent {t.title}")
        log.info("Finished importing all book torrents")
        db.commit()


def update_all_book_authors_metadata() -> None:
    with next(get_session()) as db:
        book_repository = BookRepository(db=db)
        book_service = BookService(
            book_repository=book_repository,
            torrent_service=TorrentService(
                torrent_repository=TorrentRepository(db=db)
            ),
            indexer_service=IndexerService(
                indexer_repository=IndexerRepository(db=db)
            ),
            notification_service=NotificationService(
                notification_repository=NotificationRepository(db=db)
            ),
        )

        log.info("Updating metadata for all book authors")
        authors = book_repository.get_authors()
        log.info(f"Found {len(authors)} book authors to update")

        for author in authors:
            try:
                if author.metadata_provider == "openlibrary":
                    metadata_provider = OpenLibraryMetadataProvider()
                else:
                    log.error(
                        f"Unsupported metadata provider {author.metadata_provider} for author {author.name}, skipping update."
                    )
                    continue
            except Exception:
                log.exception(
                    f"Error initializing metadata provider {author.metadata_provider} for author {author.name}",
                )
                continue
            book_service.update_author_metadata(
                db_author=author, metadata_provider=metadata_provider
            )
        db.commit()
