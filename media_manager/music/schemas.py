import typing
import uuid
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from media_manager.auth.schemas import UserRead
from media_manager.torrent.models import Quality
from media_manager.torrent.schemas import TorrentId, TorrentStatus

ArtistId = typing.NewType("ArtistId", UUID)
AlbumId = typing.NewType("AlbumId", UUID)
TrackId = typing.NewType("TrackId", UUID)
AlbumRequestId = typing.NewType("AlbumRequestId", UUID)


class Track(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: TrackId = Field(default_factory=lambda: TrackId(uuid.uuid4()))
    number: int
    external_id: str
    title: str
    duration_ms: int | None = None


class Album(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: AlbumId = Field(default_factory=lambda: AlbumId(uuid.uuid4()))
    external_id: str
    name: str
    year: int | None
    album_type: str = "album"

    tracks: list[Track]


class Artist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ArtistId = Field(default_factory=lambda: ArtistId(uuid.uuid4()))

    name: str
    overview: str
    external_id: str
    metadata_provider: str

    library: str = "Default"
    country: str | None = None
    disambiguation: str | None = None

    albums: list[Album]


class AlbumRequestBase(BaseModel):
    min_quality: Quality
    wanted_quality: Quality

    @model_validator(mode="after")
    def ensure_wanted_quality_is_eq_or_gt_min_quality(self) -> "AlbumRequestBase":
        if self.min_quality.value < self.wanted_quality.value:
            msg = "wanted_quality must be equal to or lower than minimum_quality."
            raise ValueError(msg)
        return self


class CreateAlbumRequest(AlbumRequestBase):
    album_id: AlbumId


class UpdateAlbumRequest(AlbumRequestBase):
    id: AlbumRequestId


class AlbumRequest(AlbumRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: AlbumRequestId = Field(
        default_factory=lambda: AlbumRequestId(uuid.uuid4())
    )

    album_id: AlbumId
    requested_by: UserRead | None = None
    authorized: bool = False
    authorized_by: UserRead | None = None


class RichAlbumRequest(AlbumRequest):
    artist: Artist
    album: Album


class AlbumFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    album_id: AlbumId
    quality: Quality
    torrent_id: TorrentId | None
    file_path_suffix: str


class PublicAlbumFile(AlbumFile):
    downloaded: bool = False


class AlbumTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    torrent_id: TorrentId
    torrent_title: str
    status: TorrentStatus
    quality: Quality
    imported: bool
    file_path_suffix: str
    usenet: bool


class PublicAlbum(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: AlbumId
    external_id: str
    name: str
    year: int | None
    album_type: str

    downloaded: bool = False
    tracks: list[Track]


class PublicArtist(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ArtistId

    name: str
    overview: str
    external_id: str
    metadata_provider: str

    library: str
    country: str | None = None
    disambiguation: str | None = None

    albums: list[PublicAlbum]


class RichAlbumTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    torrent_id: TorrentId
    torrent_title: str
    status: TorrentStatus
    quality: Quality
    imported: bool
    usenet: bool

    file_path_suffix: str


class RichArtistTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    artist_id: ArtistId
    name: str
    metadata_provider: str
    torrents: list[RichAlbumTorrent]
