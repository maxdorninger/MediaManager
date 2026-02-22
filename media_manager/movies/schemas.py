import typing
import uuid
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from media_manager.torrent.models import Quality
from media_manager.torrent.schemas import TorrentId, TorrentStatus

MovieId = typing.NewType("MovieId", UUID)


class Movie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: MovieId = Field(default_factory=lambda: MovieId(uuid.uuid4()))
    name: str
    overview: str
    year: int | None

    external_id: int
    metadata_provider: str
    library: str = "Default"
    original_language: str | None = None
    imdb_id: str | None = None


class MovieFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: MovieId
    file_path_suffix: str
    quality: Quality
    torrent_id: TorrentId | None = None


class PublicMovieFile(MovieFile):
    imported: bool = False


class MovieTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    torrent_id: TorrentId
    torrent_title: str
    status: TorrentStatus
    quality: Quality
    imported: bool
    file_path_suffix: str
    usenet: bool


class PublicMovie(Movie):
    downloaded: bool = False
    torrents: list[MovieTorrent] = []


class RichMovieTorrent(BaseModel):
    movie_id: MovieId
    name: str
    year: int | None
    metadata_provider: str
    torrents: list[MovieTorrent]
