from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_manager.indexer.schemas import IndexerQueryResult
    from media_manager.usenet.schemas import NzbStatus, Nzb


class AbstractDownloadClient(ABC):
    """
    Abstract base class for download clients.
    Defines the interface that all download clients must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def download_nzb(self, nzb: IndexerQueryResult) -> Nzb:
        """
        Add a nzb to the download client and return the nzb object.

        :param nzb: The indexer query result of the nzb file to download.
        :return: The nzb object with calculated hash and initial status.
        """
        pass

    @abstractmethod
    def remove_nzb(self, nzb: Nzb, delete_data: bool = False) -> None:
        """
        Remove a nzb from the download client.

        :param nzb: The nzb to remove.
        :param delete_data: Whether to delete the downloaded data.
        """
        pass

    @abstractmethod
    def get_nzb_status(self, nzb: Nzb) -> NzbStatus:
        """
        Get the status of a specific nzb.

        :param nzb: The nzb to get the status of.
        :return: The status of the nzb.
        """
        pass

    @abstractmethod
    def pause_nzb(self, nzb: Nzb) -> None:
        """
        Pause a nzb download.

        :param nzb: The nzb to pause.
        """
        pass

    @abstractmethod
    def resume_nzb(self, nzb: Nzb) -> None:
        """
        Resume a nzb download.

        :param nzb: The nzb to resume.
        """
        pass
