from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.auth.db import User
from media_manager.database import Base
from media_manager.torrent.models import Quality


class Artist(Base):
    __tablename__ = "artist"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[str]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str]
    library: Mapped[str] = mapped_column(default="")
    country: Mapped[str | None] = mapped_column(default=None)
    disambiguation: Mapped[str | None] = mapped_column(default=None)

    albums: Mapped[list["Album"]] = relationship(
        back_populates="artist", cascade="all, delete"
    )


class Album(Base):
    __tablename__ = "album"
    __table_args__ = (UniqueConstraint("artist_id", "external_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    artist_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="artist.id", ondelete="CASCADE"),
    )
    external_id: Mapped[str]
    name: Mapped[str]
    year: Mapped[int | None]
    album_type: Mapped[str] = mapped_column(default="album")

    artist: Mapped["Artist"] = relationship(back_populates="albums")
    tracks: Mapped[list["Track"]] = relationship(
        back_populates="album", cascade="all, delete"
    )

    album_files = relationship(
        "AlbumFile", back_populates="album", cascade="all, delete"
    )
    album_requests = relationship(
        "AlbumRequest", back_populates="album", cascade="all, delete"
    )


class Track(Base):
    __tablename__ = "track"
    __table_args__ = (UniqueConstraint("album_id", "number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    album_id: Mapped[UUID] = mapped_column(
        ForeignKey("album.id", ondelete="CASCADE"),
    )
    number: Mapped[int]
    external_id: Mapped[str]
    title: Mapped[str]
    duration_ms: Mapped[int | None] = mapped_column(default=None)

    album: Mapped["Album"] = relationship(back_populates="tracks")


class AlbumFile(Base):
    __tablename__ = "album_file"
    __table_args__ = (PrimaryKeyConstraint("album_id", "file_path_suffix"),)

    album_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="album.id", ondelete="CASCADE"),
    )
    torrent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="torrent.id", ondelete="SET NULL"),
    )
    file_path_suffix: Mapped[str]
    quality: Mapped[Quality]

    torrent = relationship("Torrent", back_populates="album_files", uselist=False)
    album = relationship("Album", back_populates="album_files", uselist=False)


class AlbumRequest(Base):
    __tablename__ = "album_request"
    __table_args__ = (UniqueConstraint("album_id", "wanted_quality"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    album_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="album.id", ondelete="CASCADE"),
    )
    wanted_quality: Mapped[Quality]
    min_quality: Mapped[Quality]
    requested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )
    authorized: Mapped[bool] = mapped_column(default=False)
    authorized_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )

    requested_by: Mapped["User|None"] = relationship(
        foreign_keys=[requested_by_id], uselist=False
    )
    authorized_by: Mapped["User|None"] = relationship(
        foreign_keys=[authorized_by_id], uselist=False
    )
    album = relationship("Album", back_populates="album_requests", uselist=False)
