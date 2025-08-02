import typing
import uuid
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator

from media_manager.auth.schemas import UserRead
from media_manager.torrent.models import Quality
from media_manager.torrent.schemas import TorrentId, TorrentStatus

MovieId = typing.NewType("MovieId", UUID)
MovieRequestId = typing.NewType("MovieRequestId", UUID)


class Movie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: MovieId = Field(default_factory=uuid.uuid4)
    name: str
    overview: str
    year: int | None

    external_id: int
    metadata_provider: str
    library: str = "Default"


class MovieFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: MovieId
    file_path_suffix: str
    quality: Quality
    torrent_id: TorrentId | None = None


class PublicMovieFile(MovieFile):
    downloaded: bool = False


class MovieRequestBase(BaseModel):
    min_quality: Quality
    wanted_quality: Quality

    @model_validator(mode="after")
    def ensure_wanted_quality_is_eq_or_gt_min_quality(self) -> "MovieRequestBase":
        if self.min_quality.value < self.wanted_quality.value:
            raise ValueError(
                "wanted_quality must be equal to or lower than minimum_quality."
            )
        return self


class CreateMovieRequest(MovieRequestBase):
    movie_id: MovieId


class MovieRequest(MovieRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: MovieRequestId = Field(default_factory=uuid.uuid4)

    movie_id: MovieId

    requested_by: UserRead | None = None
    authorized: bool = False
    authorized_by: UserRead | None = None


class RichMovieRequest(MovieRequest):
    movie: Movie


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
