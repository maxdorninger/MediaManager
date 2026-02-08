import logging
from abc import ABC, abstractmethod

from media_manager.config import MediaManagerConfig
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.music.schemas import Artist

log = logging.getLogger(__name__)


class AbstractMusicMetadataProvider(ABC):
    storage_path = MediaManagerConfig().misc.image_directory

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_artist_metadata(self, artist_id: str) -> Artist:
        raise NotImplementedError()

    @abstractmethod
    def search_artist(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        raise NotImplementedError()

    @abstractmethod
    def download_artist_cover_image(self, artist: Artist) -> bool:
        """
        Downloads the cover image for an artist.
        :param artist: The artist to download the cover image for.
        :return: True if the image was downloaded successfully, False otherwise.
        """
        raise NotImplementedError()
