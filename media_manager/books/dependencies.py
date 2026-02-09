from typing import Annotated

from fastapi import Depends, HTTPException, Path

from media_manager.books.repository import BookRepository
from media_manager.books.schemas import Author, AuthorId, Book, BookId
from media_manager.books.service import BookService
from media_manager.database import DbSessionDependency
from media_manager.exceptions import NotFoundError
from media_manager.indexer.dependencies import indexer_service_dep
from media_manager.notification.dependencies import notification_service_dep
from media_manager.torrent.dependencies import torrent_service_dep


def get_book_repository(db_session: DbSessionDependency) -> BookRepository:
    return BookRepository(db_session)


book_repository_dep = Annotated[BookRepository, Depends(get_book_repository)]


def get_book_service(
    book_repository: book_repository_dep,
    torrent_service: torrent_service_dep,
    indexer_service: indexer_service_dep,
    notification_service: notification_service_dep,
) -> BookService:
    return BookService(
        book_repository=book_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
        notification_service=notification_service,
    )


book_service_dep = Annotated[BookService, Depends(get_book_service)]


def get_author_by_id(
    book_service: book_service_dep,
    author_id: AuthorId = Path(..., description="The ID of the author"),
) -> Author:
    try:
        author = book_service.get_author_by_id(author_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Author with ID {author_id} not found.",
        ) from None
    return author


author_dep = Annotated[Author, Depends(get_author_by_id)]


def get_book_by_id(
    book_service: book_service_dep,
    book_id: BookId = Path(..., description="The ID of the book"),
) -> Book:
    try:
        book = book_service.book_repository.get_book(book_id=book_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Book with ID {book_id} not found.",
        ) from None
    return book


book_dep = Annotated[Book, Depends(get_book_by_id)]
