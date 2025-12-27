import typing
import uuid
from enum import Enum

from pydantic import ConfigDict, BaseModel, Field

TorrentId = typing.NewType("TorrentId", uuid.UUID)


class Quality(Enum):
    uhd = 1
    fullhd = 2
    hd = 3
    sd = 4
    unknown = 5


class QualityStrings(Enum):
    uhd = "4K"
    fullhd = "1080p"
    hd = "720p"
    sd = "400p"
    unknown = "unknown"


class TorrentStatus(Enum):
    finished = 1
    # Torrent is finished downloading and ready to move.
    downloading = 2
    # Torrent is downloading.
    error = 3
    # Torrent failed to download.
    unknown = 4
    # Unable to obtain status of torrent.


class Torrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: TorrentId = Field(default_factory=uuid.uuid4)
    status: TorrentStatus
    title: str
    quality: Quality
    imported: bool
    hash: str
    usenet: bool = False
