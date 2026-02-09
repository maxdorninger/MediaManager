import enum
import typing
import uuid
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from media_manager.auth.schemas import UserRead
from media_manager.torrent.models import Quality
from media_manager.torrent.schemas import TorrentId, TorrentStatus

AuthorId = typing.NewType("AuthorId", UUID)
BookId = typing.NewType("BookId", UUID)
BookRequestId = typing.NewType("BookRequestId", UUID)


class BookFormat(str, enum.Enum):
    ebook = "ebook"
    audiobook = "audiobook"


class Book(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: BookId = Field(default_factory=lambda: BookId(uuid.uuid4()))
    external_id: str
    name: str
    year: int | None
    format: BookFormat = BookFormat.ebook
    isbn: str | None = None
    publisher: str | None = None
    page_count: int | None = None


class Author(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: AuthorId = Field(default_factory=lambda: AuthorId(uuid.uuid4()))

    name: str
    overview: str
    external_id: str
    metadata_provider: str

    library: str = "Default"

    books: list[Book]


class BookRequestBase(BaseModel):
    min_quality: Quality
    wanted_quality: Quality

    @model_validator(mode="after")
    def ensure_wanted_quality_is_eq_or_gt_min_quality(self) -> "BookRequestBase":
        if self.min_quality.value < self.wanted_quality.value:
            msg = "wanted_quality must be equal to or lower than minimum_quality."
            raise ValueError(msg)
        return self


class CreateBookRequest(BookRequestBase):
    book_id: BookId


class UpdateBookRequest(BookRequestBase):
    id: BookRequestId


class BookRequest(BookRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: BookRequestId = Field(
        default_factory=lambda: BookRequestId(uuid.uuid4())
    )

    book_id: BookId
    requested_by: UserRead | None = None
    authorized: bool = False
    authorized_by: UserRead | None = None


class RichBookRequest(BookRequest):
    author: Author
    book: Book


class BookFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    book_id: BookId
    quality: Quality
    torrent_id: TorrentId | None
    file_path_suffix: str


class PublicBookFile(BookFile):
    downloaded: bool = False


class BookTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    torrent_id: TorrentId
    torrent_title: str
    status: TorrentStatus
    quality: Quality
    imported: bool
    file_path_suffix: str
    usenet: bool


class PublicBook(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: BookId
    external_id: str
    name: str
    year: int | None
    format: BookFormat
    isbn: str | None = None
    publisher: str | None = None
    page_count: int | None = None

    downloaded: bool = False


class PublicAuthor(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: AuthorId

    name: str
    overview: str
    external_id: str
    metadata_provider: str

    library: str

    books: list[PublicBook]


class RichBookTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    torrent_id: TorrentId
    torrent_title: str
    status: TorrentStatus
    quality: Quality
    imported: bool
    usenet: bool

    file_path_suffix: str


class RichAuthorTorrent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author_id: AuthorId
    name: str
    metadata_provider: str
    torrents: list[RichBookTorrent]
