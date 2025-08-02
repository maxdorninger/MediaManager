import typing
import uuid
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, model_validator

from media_manager.auth.schemas import UserRead
from media_manager.torrent.models import Quality
from media_manager.torrent.schemas import TorrentId, TorrentStatus

ShowId = typing.NewType("ShowId", UUID)
SeasonId = typing.NewType("SeasonId", UUID)
EpisodeId = typing.NewType("EpisodeId", UUID)

SeasonNumber = typing.NewType("SeasonNumber", int)
EpisodeNumber = typing.NewType("EpisodeNumber", int)
SeasonRequestId = typing.NewType("SeasonRequestId", UUID)


class Episode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EpisodeId = Field(default_factory=uuid.uuid4)
    number: EpisodeNumber
    external_id: int
    title: str


class Season(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: SeasonId = Field(default_factory=uuid.uuid4)
    number: SeasonNumber

    name: str
    overview: str

    external_id: int

    episodes: list[Episode]


class Show(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ShowId = Field(default_factory=uuid.uuid4)

    name: str
    overview: str
    year: int | None

    ended: bool = False
    external_id: int
    metadata_provider: str

    continuous_download: bool = False
    library: str = "Default"

    seasons: list[Season]


class SeasonRequestBase(BaseModel):
    min_quality: Quality
    wanted_quality: Quality

    @model_validator(mode="after")
    def ensure_wanted_quality_is_eq_or_gt_min_quality(self) -> "SeasonRequestBase":
        if self.min_quality.value < self.wanted_quality.value:
            raise ValueError(
                "wanted_quality must be equal to or lower than minimum_quality."
            )
        return self


class CreateSeasonRequest(SeasonRequestBase):
    season_id: SeasonId
    pass


class UpdateSeasonRequest(SeasonRequestBase):
    id: SeasonRequestId


class SeasonRequest(SeasonRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: SeasonRequestId = Field(default_factory=uuid.uuid4)

    season_id: SeasonId
    requested_by: UserRead | None = None
    authorized: bool = False
    authorized_by: UserRead | None = None


class RichSeasonRequest(SeasonRequest):
    show: Show
    season: Season


class SeasonFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    season_id: SeasonId
    quality: Quality
    torrent_id: TorrentId | None
    file_path_suffix: str


class PublicSeasonFile(SeasonFile):
    downloaded: bool = False


class RichSeasonTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    torrent_id: TorrentId
    torrent_title: str
    status: TorrentStatus
    quality: Quality
    imported: bool
    usenet: bool

    file_path_suffix: str
    seasons: list[SeasonNumber]


class RichShowTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    show_id: ShowId
    name: str
    year: int | None
    metadata_provider: str
    torrents: list[RichSeasonTorrent]


class PublicSeason(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: SeasonId
    number: SeasonNumber

    downloaded: bool = False
    name: str
    overview: str

    external_id: int

    episodes: list[Episode]


class PublicShow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ShowId

    name: str
    overview: str
    year: int | None

    external_id: int
    metadata_provider: str

    ended: bool = False
    continuous_download: bool = False
    library: str

    seasons: list[PublicSeason]
