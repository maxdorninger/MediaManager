from uuid import UUID
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.database import Base
from media_manager.torrent.models import Quality


class Artist(Base):
    __tablename__ = "artist"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)
    
    # Common media fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str]
    year: Mapped[int | None]
    library: Mapped[str] = mapped_column(default="")
    
    # Artist-specific fields
    genres: Mapped[str] = mapped_column(default="")
    country: Mapped[str] = mapped_column(default="")
    
    albums: Mapped[list["Album"]] = relationship(
        back_populates="artist", cascade="all, delete"
    )


class Album(Base):
    __tablename__ = "album"
    __table_args__ = (
        UniqueConstraint("artist_id", "name", "year"),
        UniqueConstraint("external_id", "metadata_provider"),
    )
    
    # Common media fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str]
    year: Mapped[int | None]
    library: Mapped[str] = mapped_column(default="")
    
    # Album-specific fields
    artist_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="artist.id", ondelete="CASCADE"),
    )
    release_date: Mapped[str] = mapped_column(default="")
    album_type: Mapped[str] = mapped_column(default="album")  # album, single, ep
    
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
    __table_args__ = (
        UniqueConstraint("album_id", "track_number"),
        UniqueConstraint("external_id", "metadata_provider"),
    )
    
    # Common media fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str] = mapped_column(default="")  # Track description
    year: Mapped[int | None]
    library: Mapped[str] = mapped_column(default="")
    
    # Track-specific fields
    album_id: Mapped[UUID] = mapped_column(
        ForeignKey("album.id", ondelete="CASCADE"),
    )
    track_number: Mapped[int]
    duration: Mapped[int] = mapped_column(default=0)  # in seconds
    
    album: Mapped["Album"] = relationship(back_populates="tracks")


class AlbumFile(Base):
    __tablename__ = "album_file"
    __table_args__ = (PrimaryKeyConstraint("album_id", "file_path_suffix"),)
    
    # Common media file fields
    album_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="album.id", ondelete="CASCADE"),
    )
    file_path_suffix: Mapped[str]
    quality: Mapped[Quality]
    torrent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="torrent.id", ondelete="SET NULL"),
    )
    
    torrent = relationship("Torrent", uselist=False)
    album = relationship("Album", back_populates="album_files", uselist=False)


class AlbumRequest(Base):
    __tablename__ = "album_request"
    __table_args__ = (UniqueConstraint("album_id", "wanted_quality"),)
    
    # Common media request fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    wanted_quality: Mapped[Quality]
    min_quality: Mapped[Quality]
    authorized: Mapped[bool] = mapped_column(default=False)
    
    requested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )
    authorized_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )
    
    # Album-specific fields
    album_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="album.id", ondelete="CASCADE"),
    )
    
    requested_by = relationship(
        "User", 
        foreign_keys=[requested_by_id], 
        uselist=False
    )
    authorized_by = relationship(
        "User", 
        foreign_keys=[authorized_by_id], 
        uselist=False
    )
    album = relationship("Album", back_populates="album_requests", uselist=False)