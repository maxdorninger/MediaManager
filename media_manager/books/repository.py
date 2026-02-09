import logging

from sqlalchemy import delete, select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session, joinedload

from media_manager.books.models import Author, Book, BookFile, BookRequest
from media_manager.books.schemas import (
    Author as AuthorSchema,
)
from media_manager.books.schemas import (
    AuthorId,
    BookId,
    BookRequestId,
)
from media_manager.books.schemas import (
    BookFile as BookFileSchema,
)
from media_manager.books.schemas import (
    BookRequest as BookRequestSchema,
)
from media_manager.books.schemas import (
    BookTorrent as BookTorrentSchema,
)
from media_manager.books.schemas import (
    RichBookRequest as RichBookRequestSchema,
)
from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import TorrentId

log = logging.getLogger(__name__)


class BookRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_author_by_id(self, author_id: AuthorId) -> AuthorSchema:
        try:
            stmt = (
                select(Author)
                .options(joinedload(Author.books))
                .where(Author.id == author_id)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Author with id {author_id} not found."
                raise NotFoundError(msg)
            return AuthorSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while retrieving author {author_id}")
            raise

    def get_author_by_external_id(
        self, external_id: str, metadata_provider: str
    ) -> AuthorSchema:
        try:
            stmt = (
                select(Author)
                .options(joinedload(Author.books))
                .where(Author.external_id == external_id)
                .where(Author.metadata_provider == metadata_provider)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Author with external_id {external_id} and provider {metadata_provider} not found."
                raise NotFoundError(msg)
            return AuthorSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error while retrieving author by external_id {external_id}"
            )
            raise

    def get_authors(self) -> list[AuthorSchema]:
        try:
            stmt = select(Author).options(joinedload(Author.books))
            results = self.db.execute(stmt).scalars().unique().all()
            return [AuthorSchema.model_validate(author) for author in results]
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while retrieving all authors")
            raise

    def save_author(self, author: AuthorSchema) -> AuthorSchema:
        log.debug(f"Attempting to save author: {author.name} (ID: {author.id})")
        db_author = self.db.get(Author, author.id) if author.id else None

        if db_author:
            log.debug(f"Updating existing author with ID: {author.id}")
            db_author.external_id = author.external_id
            db_author.metadata_provider = author.metadata_provider
            db_author.name = author.name
            db_author.overview = author.overview
        else:
            log.debug(f"Creating new author: {author.name}")
            author_data = author.model_dump(exclude={"books"})
            db_author = Author(**author_data)
            self.db.add(db_author)

            for book in author.books:
                book_data = book.model_dump()
                book_data["author_id"] = db_author.id
                db_book = Book(**book_data)
                self.db.add(db_book)

        try:
            self.db.commit()
            self.db.refresh(db_author)
            log.info(f"Successfully saved author: {db_author.name} (ID: {db_author.id})")
            return self.get_author_by_id(AuthorId(db_author.id))
        except IntegrityError as e:
            self.db.rollback()
            log.exception(f"Integrity error while saving author {author.name}")
            msg = f"Author with this primary key or unique constraint violation: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while saving author {author.name}")
            raise

    def delete_author(self, author_id: AuthorId) -> None:
        log.debug(f"Attempting to delete author with id: {author_id}")
        try:
            author = self.db.get(Author, author_id)
            if not author:
                log.warning(f"Author with id {author_id} not found for deletion.")
                msg = f"Author with id {author_id} not found."
                raise NotFoundError(msg)
            self.db.delete(author)
            self.db.commit()
            log.info(f"Successfully deleted author with id: {author_id}")
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while deleting author {author_id}")
            raise

    def set_author_library(self, author_id: AuthorId, library: str) -> None:
        try:
            author = self.db.get(Author, author_id)
            if not author:
                msg = f"Author with id {author_id} not found."
                raise NotFoundError(msg)
            author.library = library
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error setting library for author {author_id}")
            raise

    def update_author_attributes(
        self,
        author_id: AuthorId,
        name: str | None = None,
        overview: str | None = None,
    ) -> AuthorSchema:
        db_author = self.db.get(Author, author_id)
        if not db_author:
            msg = f"Author with id {author_id} not found."
            raise NotFoundError(msg)

        updated = False
        if name is not None and db_author.name != name:
            db_author.name = name
            updated = True
        if overview is not None and db_author.overview != overview:
            db_author.overview = overview
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_author)
        return self.get_author_by_id(AuthorId(db_author.id))

    def get_book(self, book_id: BookId) -> "Book":
        from media_manager.books.schemas import Book as BookSchema

        try:
            stmt = select(Book).where(Book.id == book_id)
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Book with id {book_id} not found."
                raise NotFoundError(msg)
            return BookSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while retrieving book {book_id}")
            raise

    # -------------------------------------------------------------------------
    # BOOK REQUESTS
    # -------------------------------------------------------------------------

    def add_book_request(
        self, book_request: BookRequestSchema
    ) -> BookRequestSchema:
        db_model = BookRequest(
            id=book_request.id,
            book_id=book_request.book_id,
            requested_by_id=book_request.requested_by.id
            if book_request.requested_by
            else None,
            authorized_by_id=book_request.authorized_by.id
            if book_request.authorized_by
            else None,
            wanted_quality=book_request.wanted_quality,
            min_quality=book_request.min_quality,
            authorized=book_request.authorized,
        )
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            log.info(f"Successfully added book request with id: {db_model.id}")
            return BookRequestSchema.model_validate(db_model)
        except IntegrityError:
            self.db.rollback()
            log.exception("Integrity error while adding book request")
            raise
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while adding book request")
            raise

    def delete_book_request(self, book_request_id: BookRequestId) -> None:
        try:
            stmt = delete(BookRequest).where(BookRequest.id == book_request_id)
            result = self.db.execute(stmt)
            if result.rowcount == 0:
                self.db.rollback()
                msg = f"Book request with id {book_request_id} not found."
                raise NotFoundError(msg)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error while deleting book request {book_request_id}"
            )
            raise

    def get_book_requests(self) -> list[RichBookRequestSchema]:
        try:
            stmt = select(BookRequest).options(
                joinedload(BookRequest.requested_by),
                joinedload(BookRequest.authorized_by),
                joinedload(BookRequest.book).joinedload(Book.author),
            )
            results = self.db.execute(stmt).scalars().unique().all()
            rich_results = []
            for req in results:
                book_schema = self.get_book(BookId(req.book_id))
                author_schema = self.get_author_by_id(AuthorId(req.book.author_id))
                rich_results.append(
                    RichBookRequestSchema(
                        id=req.id,
                        book_id=req.book_id,
                        wanted_quality=req.wanted_quality,
                        min_quality=req.min_quality,
                        requested_by=req.requested_by,
                        authorized=req.authorized,
                        authorized_by=req.authorized_by,
                        book=book_schema,
                        author=author_schema,
                    )
                )
            return rich_results
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while retrieving book requests")
            raise

    def get_book_request(self, book_request_id: BookRequestId) -> BookRequestSchema:
        try:
            request = self.db.get(BookRequest, book_request_id)
            if not request:
                msg = f"Book request with id {book_request_id} not found."
                raise NotFoundError(msg)
            return BookRequestSchema.model_validate(request)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error retrieving book request {book_request_id}")
            raise

    # -------------------------------------------------------------------------
    # BOOK FILES
    # -------------------------------------------------------------------------

    def add_book_file(self, book_file: BookFileSchema) -> BookFileSchema:
        db_model = BookFile(**book_file.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            return BookFileSchema.model_validate(db_model)
        except IntegrityError:
            self.db.rollback()
            log.exception("Integrity error while adding book file")
            raise
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while adding book file")
            raise

    def remove_book_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        try:
            stmt = delete(BookFile).where(BookFile.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error removing book files for torrent_id {torrent_id}"
            )
            raise
        return result.rowcount

    def get_book_files_by_book_id(self, book_id: BookId) -> list[BookFileSchema]:
        try:
            stmt = select(BookFile).where(BookFile.book_id == book_id)
            results = self.db.execute(stmt).scalars().all()
            return [BookFileSchema.model_validate(bf) for bf in results]
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error retrieving book files for book_id {book_id}"
            )
            raise

    # -------------------------------------------------------------------------
    # TORRENTS
    # -------------------------------------------------------------------------

    def get_torrents_by_author_id(
        self, author_id: AuthorId
    ) -> list[BookTorrentSchema]:
        try:
            stmt = (
                select(Torrent, BookFile.file_path_suffix)
                .distinct()
                .join(BookFile, BookFile.torrent_id == Torrent.id)
                .join(Book, Book.id == BookFile.book_id)
                .where(Book.author_id == author_id)
            )
            results = self.db.execute(stmt).all()
            formatted_results = []
            for torrent, file_path_suffix in results:
                book_torrent = BookTorrentSchema(
                    torrent_id=torrent.id,
                    torrent_title=torrent.title,
                    status=torrent.status,
                    quality=torrent.quality,
                    imported=torrent.imported,
                    file_path_suffix=file_path_suffix,
                    usenet=torrent.usenet,
                )
                formatted_results.append(book_torrent)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error retrieving torrents for author_id {author_id}"
            )
            raise
        return formatted_results

    def get_all_authors_with_torrents(self) -> list[AuthorSchema]:
        try:
            stmt = (
                select(Author)
                .distinct()
                .join(Book, Author.id == Book.author_id)
                .join(BookFile, Book.id == BookFile.book_id)
                .join(Torrent, BookFile.torrent_id == Torrent.id)
                .options(joinedload(Author.books))
                .order_by(Author.name)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [AuthorSchema.model_validate(author) for author in results]
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error retrieving all authors with torrents")
            raise

    def get_author_by_torrent_id(self, torrent_id: TorrentId) -> AuthorSchema | None:
        try:
            stmt = (
                select(Author)
                .join(Book, Author.id == Book.author_id)
                .join(BookFile, Book.id == BookFile.book_id)
                .where(BookFile.torrent_id == torrent_id)
                .options(joinedload(Author.books))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                return None
            return AuthorSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error retrieving author by torrent_id {torrent_id}"
            )
            raise
