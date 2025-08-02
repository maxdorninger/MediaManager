from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID
import uuid

from pydantic import BaseModel, Field, ConfigDict, model_validator


class BaseMediaSchema(BaseModel, ABC):
    """
    Abstract base schema for all media types
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid.uuid4)
    name: str
    overview: str
    year: Optional[int]
    external_id: int
    metadata_provider: str
    library: str = "Default"


class BaseMediaFileSchema(BaseModel, ABC):
    """
    Abstract base schema for media files
    """
    model_config = ConfigDict(from_attributes=True)
    
    file_path_suffix: str
    quality: str  # Use string instead of Quality enum to avoid circular import
    torrent_id: Optional[UUID] = None


class BaseMediaRequestSchema(BaseModel, ABC):
    """
    Abstract base schema for media requests
    """
    min_quality: str  # Use string instead of Quality enum to avoid circular import
    wanted_quality: str  # Use string instead of Quality enum to avoid circular import


class BaseCreateMediaRequestSchema(BaseMediaRequestSchema, ABC):
    """
    Abstract base schema for creating media requests
    """
    pass


class BaseMediaRequestWithUserSchema(BaseMediaRequestSchema, ABC):
    """
    Abstract base schema for media requests with user information
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid.uuid4)
    requested_by: Optional[Dict[str, Any]] = None  # Use dict to avoid import
    authorized: bool = False
    authorized_by: Optional[Dict[str, Any]] = None  # Use dict to avoid import


class MediaPluginInfo(BaseModel):
    """
    Information about a media plugin
    """
    name: str
    display_name: str
    version: str
    description: str
    media_type: str
    supported_extensions: List[str]
    metadata_providers: List[str]
    
    
class MediaPluginConfig(BaseModel):
    """
    Configuration for a media plugin
    """
    enabled: bool = True
    libraries: List[Dict[str, Any]] = []
    settings: Dict[str, Any] = {}