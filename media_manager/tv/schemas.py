import typing
import uuid
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from media_manager.torrent.models import Quality
from media_manager.torrent.schemas import TorrentId, TorrentStatus

ShowId = typing.NewType("ShowId", UUID)
SeasonId = typing.NewType("SeasonId", UUID)
EpisodeId = typing.NewType("EpisodeId", UUID)

SeasonNumber = typing.NewType("SeasonNumber", int)
EpisodeNumber = typing.NewType("EpisodeNumber", int)


class Episode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: EpisodeId = Field(default_factory=lambda: EpisodeId(uuid.uuid4()))
    number: EpisodeNumber
    external_id: int
    title: str
    overview: str | None = None


class Season(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: SeasonId = Field(default_factory=lambda: SeasonId(uuid.uuid4()))
    number: SeasonNumber

    name: str
    overview: str

    external_id: int

    episodes: list[Episode]


class Show(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ShowId = Field(default_factory=lambda: ShowId(uuid.uuid4()))

    name: str
    overview: str
    year: int | None

    ended: bool = False
    external_id: int
    metadata_provider: str

    continuous_download: bool = False
    library: str = "Default"
    original_language: str | None = None

    imdb_id: str | None = None

    seasons: list[Season]


class EpisodeFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    episode_id: EpisodeId
    quality: Quality
    torrent_id: TorrentId | None
    file_path_suffix: str


class PublicEpisodeFile(EpisodeFile):
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
    episodes: list[EpisodeNumber]


class RichShowTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    show_id: ShowId
    name: str
    year: int | None
    metadata_provider: str
    torrents: list[RichSeasonTorrent]


class PublicEpisode(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: EpisodeId
    number: EpisodeNumber

    downloaded: bool = False
    title: str
    overview: str | None = None

    external_id: int


class PublicSeason(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: SeasonId
    number: SeasonNumber

    downloaded: bool = False
    name: str
    overview: str

    external_id: int

    episodes: list[PublicEpisode]


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
