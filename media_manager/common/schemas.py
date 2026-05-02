import uuid
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from media_manager.torrent.models import Quality


class BaseMedia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid.uuid4)
    name: str
    overview: str
    year: int | None
    external_id: int
    metadata_provider: str
    library: str = "Default"
    original_language: str | None = None
    imdb_id: str | None = None


class BaseMediaFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quality: Quality
    torrent_id: UUID | None = None
    file_path_suffix: str


class PublicMediaFile(BaseMediaFile):
    downloaded: bool = False
    imported: bool = False
