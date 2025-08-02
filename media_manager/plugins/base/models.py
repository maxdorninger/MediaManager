"""
Base model definitions for media plugins.

These are abstract base classes that define common patterns for media types.
They are intended to be used as mixins or reference implementations.
Plugin models should inherit from the actual database Base class.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseMediaMixin:
    """
    Mixin class that defines common fields for all media types.
    Plugin models should inherit from both this and the database Base class.
    """
    # Common fields that all media types should have:
    # - id: UUID primary key
    # - external_id: int from metadata provider
    # - metadata_provider: str (tmdb, tvdb, etc.)
    # - name: str
    # - overview: str
    # - year: Optional[int]
    # - library: str (default="")
    
    # Table constraint: UniqueConstraint("external_id", "metadata_provider")
    pass


class BaseMediaFileMixin:
    """
    Mixin class that defines common fields for media files.
    """
    # Common fields for media files:
    # - file_path_suffix: str
    # - quality: Quality enum
    # - torrent_id: Optional[UUID] with FK to torrent.id
    pass


class BaseMediaRequestMixin:
    """
    Mixin class that defines common fields for media requests.
    """
    # Common fields for media requests:
    # - id: UUID primary key
    # - wanted_quality: Quality enum
    # - min_quality: Quality enum
    # - authorized: bool (default=False)
    # - requested_by_id: Optional[UUID] with FK to user.id
    # - authorized_by_id: Optional[UUID] with FK to user.id
    pass


# Keep these as documentation/reference
class AbstractMediaModel(ABC):
    """
    Abstract interface that all media models should implement.
    This is for type hints and documentation purposes.
    """
    
    @abstractmethod
    def get_display_name(self) -> str:
        """Return a human-readable name for this media item"""
        pass
    
    @abstractmethod
    def get_metadata_info(self) -> Dict[str, Any]:
        """Return metadata information as a dictionary"""
        pass


class AbstractMediaFileModel(ABC):
    """
    Abstract interface that all media file models should implement.
    """
    
    @abstractmethod
    def get_full_path(self, base_directory: str) -> str:
        """Return the full file path given a base directory"""
        pass


class AbstractMediaRequestModel(ABC):
    """
    Abstract interface that all media request models should implement.
    """
    
    @abstractmethod
    def is_downloadable(self) -> bool:
        """Return True if this request is ready for download"""
        pass