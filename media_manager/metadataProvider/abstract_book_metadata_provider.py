import logging
from abc import ABC, abstractmethod

from media_manager.books.schemas import Author, Book
from media_manager.config import MediaManagerConfig
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult

log = logging.getLogger(__name__)


class AbstractBookMetadataProvider(ABC):
    storage_path = MediaManagerConfig().misc.image_directory

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_author_metadata(self, author_id: str) -> Author:
        raise NotImplementedError()

    @abstractmethod
    def search_author(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        raise NotImplementedError()

    @abstractmethod
    def search_book(self, query: str) -> list[MetaDataProviderSearchResult]:
        raise NotImplementedError()

    @abstractmethod
    def download_author_cover_image(self, author: Author) -> bool:
        """
        Downloads the cover image for an author.
        :param author: The author to download the cover image for.
        :return: True if the image was downloaded successfully, False otherwise.
        """
        raise NotImplementedError()

    @abstractmethod
    def download_book_cover_image(self, book: Book) -> bool:
        """
        Downloads the cover image for a book.
        :param book: The book to download the cover image for.
        :return: True if the image was downloaded successfully, False otherwise.
        """
        raise NotImplementedError()
