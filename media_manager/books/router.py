from typing import Annotated

from fastapi import APIRouter, Depends, status

from media_manager.auth.schemas import UserRead
from media_manager.auth.users import current_active_user, current_superuser
from media_manager.books import log
from media_manager.books.dependencies import (
    author_dep,
    book_dep,
    book_service_dep,
)
from media_manager.books.schemas import (
    Author,
    AuthorId,
    Book,
    BookId,
    BookRequest,
    BookRequestBase,
    BookRequestId,
    CreateBookRequest,
    PublicAuthor,
    PublicBookFile,
    RichAuthorTorrent,
    RichBookRequest,
)
from media_manager.config import LibraryItem, MediaManagerConfig
from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.indexer.schemas import (
    IndexerQueryResult,
    IndexerQueryResultId,
)
from media_manager.metadataProvider.book_dependencies import (
    book_metadata_provider_dep,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.torrent.schemas import Torrent

router = APIRouter()

# -----------------------------------------------------------------------------
# METADATA & SEARCH
# -----------------------------------------------------------------------------


@router.get(
    "/search",
    dependencies=[Depends(current_active_user)],
)
def search_for_author(
    query: str,
    book_service: book_service_dep,
    metadata_provider: book_metadata_provider_dep,
) -> list[MetaDataProviderSearchResult]:
    """
    Search for an author on the configured book metadata provider.
    """
    return book_service.search_for_author(
        query=query, metadata_provider=metadata_provider
    )


@router.get(
    "/recommended",
    dependencies=[Depends(current_active_user)],
)
def get_popular_authors(
    book_service: book_service_dep,
    metadata_provider: book_metadata_provider_dep,
) -> list[MetaDataProviderSearchResult]:
    """
    Get a list of trending/popular authors from OpenLibrary.
    """
    return book_service.get_popular_authors(metadata_provider=metadata_provider)


# -----------------------------------------------------------------------------
# AUTHORS
# -----------------------------------------------------------------------------


@router.get(
    "/authors",
    dependencies=[Depends(current_active_user)],
)
def get_all_authors(book_service: book_service_dep) -> list[Author]:
    """
    Get all authors in the library.
    """
    return book_service.get_all_authors()


@router.post(
    "/authors",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_201_CREATED: {
            "model": Author,
            "description": "Successfully created author",
        }
    },
)
def add_an_author(
    book_service: book_service_dep,
    metadata_provider: book_metadata_provider_dep,
    author_id: str,
) -> Author:
    """
    Add a new author to the library.
    """
    try:
        author = book_service.add_author(
            external_id=author_id,
            metadata_provider=metadata_provider,
        )
    except ConflictError:
        author = book_service.get_author_by_external_id(
            external_id=author_id, metadata_provider=metadata_provider.name
        )
        if not author:
            raise NotFoundError from ConflictError
    return author


@router.get(
    "/authors/torrents",
    dependencies=[Depends(current_active_user)],
)
def get_all_authors_with_torrents(
    book_service: book_service_dep,
) -> list[RichAuthorTorrent]:
    """
    Get all authors that are associated with torrents.
    """
    return book_service.get_all_authors_with_torrents()


@router.get(
    "/authors/libraries",
    dependencies=[Depends(current_active_user)],
)
def get_available_libraries() -> list[LibraryItem]:
    """
    Get available book libraries from configuration.
    """
    return MediaManagerConfig().misc.books_libraries


# -----------------------------------------------------------------------------
# BOOK REQUESTS
# -----------------------------------------------------------------------------


@router.get(
    "/books/requests",
    dependencies=[Depends(current_active_user)],
)
def get_all_book_requests(
    book_service: book_service_dep,
) -> list[RichBookRequest]:
    """
    Get all book requests.
    """
    return book_service.get_all_book_requests()


@router.post(
    "/books/requests",
    status_code=status.HTTP_201_CREATED,
)
def create_book_request(
    book_service: book_service_dep,
    book_request: CreateBookRequest,
    user: Annotated[UserRead, Depends(current_active_user)],
) -> BookRequest:
    """
    Create a new book request.
    """
    log.info(
        f"User {user.email} is creating a book request for {book_request.book_id}"
    )
    book_request: BookRequest = BookRequest.model_validate(book_request)
    book_request.requested_by = user
    if user.is_superuser:
        book_request.authorized = True
        book_request.authorized_by = user

    return book_service.add_book_request(book_request=book_request)


@router.put(
    "/books/requests/{book_request_id}",
)
def update_book_request(
    book_service: book_service_dep,
    book_request_id: BookRequestId,
    update_request: BookRequestBase,
    user: Annotated[UserRead, Depends(current_active_user)],
) -> BookRequest:
    """
    Update an existing book request.
    """
    book_request = book_service.get_book_request_by_id(
        book_request_id=book_request_id
    )
    if book_request.requested_by.id != user.id or user.is_superuser:
        book_request.min_quality = update_request.min_quality
        book_request.wanted_quality = update_request.wanted_quality

    return book_service.update_book_request(book_request=book_request)


@router.patch(
    "/books/requests/{book_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def authorize_book_request(
    book_service: book_service_dep,
    book_request_id: BookRequestId,
    user: Annotated[UserRead, Depends(current_superuser)],
    authorized_status: bool = False,
) -> None:
    """
    Authorize or de-authorize a book request.
    """
    book_request = book_service.get_book_request_by_id(
        book_request_id=book_request_id
    )
    book_request.authorized = authorized_status
    if authorized_status:
        book_request.authorized_by = user
    else:
        book_request.authorized_by = None
    book_service.update_book_request(book_request=book_request)


@router.delete(
    "/books/requests/{book_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_book_request(
    book_service: book_service_dep, book_request_id: BookRequestId
) -> None:
    """
    Delete a book request.
    """
    book_service.delete_book_request(book_request_id=book_request_id)


# -----------------------------------------------------------------------------
# AUTHORS - SINGLE RESOURCE
# -----------------------------------------------------------------------------


@router.get(
    "/authors/{author_id}",
    dependencies=[Depends(current_active_user)],
)
def get_author_by_id(
    book_service: book_service_dep, author: author_dep
) -> PublicAuthor:
    """
    Get details for a specific author.
    """
    return book_service.get_public_author_by_id(author=author)


@router.delete(
    "/authors/{author_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_an_author(
    book_service: book_service_dep,
    author: author_dep,
    delete_files_on_disk: bool = False,
    delete_torrents: bool = False,
) -> None:
    """
    Delete an author from the library.
    """
    book_service.delete_author(
        author=author,
        delete_files_on_disk=delete_files_on_disk,
        delete_torrents=delete_torrents,
    )


@router.post(
    "/authors/{author_id}/metadata",
    dependencies=[Depends(current_active_user)],
)
def update_author_metadata(
    book_service: book_service_dep,
    author: author_dep,
    metadata_provider: book_metadata_provider_dep,
) -> PublicAuthor:
    """
    Refresh metadata for an author from the metadata provider.
    """
    book_service.update_author_metadata(
        db_author=author, metadata_provider=metadata_provider
    )
    updated_author = book_service.get_author_by_id(author_id=author.id)
    return book_service.get_public_author_by_id(author=updated_author)


@router.post(
    "/authors/{author_id}/library",
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_library(
    author: author_dep,
    book_service: book_service_dep,
    library: str,
) -> None:
    """
    Set the library path for an author.
    """
    book_service.set_author_library(author=author, library=library)


@router.get(
    "/authors/{author_id}/torrents",
    dependencies=[Depends(current_active_user)],
)
def get_torrents_for_author(
    book_service: book_service_dep,
    author: author_dep,
) -> RichAuthorTorrent:
    """
    Get torrents associated with an author.
    """
    return book_service.get_torrents_for_author(author=author)


# -----------------------------------------------------------------------------
# BOOKS - SINGLE RESOURCE
# -----------------------------------------------------------------------------


@router.get(
    "/books/{book_id}",
    dependencies=[Depends(current_active_user)],
)
def get_book_by_id(book: book_dep) -> Book:
    """
    Get details for a specific book.
    """
    return Book.model_validate(book)


@router.get(
    "/books/{book_id}/files",
    dependencies=[Depends(current_active_user)],
)
def get_book_files(
    book_service: book_service_dep,
    book: book_dep,
) -> list[PublicBookFile]:
    """
    Get files associated with a specific book.
    """
    return book_service.get_public_book_files(book_id=book.id)


# -----------------------------------------------------------------------------
# TORRENTS
# -----------------------------------------------------------------------------


@router.get(
    "/torrents",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
)
def search_torrents_for_book(
    book_service: book_service_dep,
    author_id: AuthorId,
    book_name: str,
    search_query_override: str | None = None,
) -> list[IndexerQueryResult]:
    """
    Search for torrents for a specific book.
    """
    author = book_service.get_author_by_id(author_id=author_id)
    return book_service.get_all_available_torrents_for_book(
        author=author,
        book_name=book_name,
        search_query_override=search_query_override,
    )


@router.post(
    "/torrents",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
)
def download_a_torrent(
    book_service: book_service_dep,
    public_indexer_result_id: IndexerQueryResultId,
    author_id: AuthorId,
    book_id: BookId,
    override_file_path_suffix: str = "",
) -> Torrent:
    """
    Download a torrent for a specific book.
    """
    author = book_service.get_author_by_id(author_id=author_id)
    return book_service.download_torrent(
        public_indexer_result_id=public_indexer_result_id,
        author=author,
        book_id=book_id,
        override_file_path_suffix=override_file_path_suffix,
    )
