from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.auth.db import User
from media_manager.database import Base
from media_manager.torrent.models import Quality


class Movie(Base):
    __tablename__ = "movie"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    imdb_id: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str]
    year: Mapped[int | None]
    library: Mapped[str] = mapped_column(default="")
    original_language: Mapped[str | None] = mapped_column(default=None)
    movie_requests: Mapped[list["MovieRequest"]] = relationship(
        "MovieRequest", back_populates="movie", cascade="all, delete-orphan"
    )


class MovieFile(Base):
    __tablename__ = "movie_file"
    __table_args__ = (PrimaryKeyConstraint("movie_id", "file_path_suffix"),)

    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="movie.id", ondelete="CASCADE"),
    )
    file_path_suffix: Mapped[str]

    quality: Mapped[Quality]
    torrent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="torrent.id", ondelete="SET NULL"),
    )

    torrent = relationship("Torrent", back_populates="movie_files", uselist=False)


class MovieRequest(Base):
    __tablename__ = "movie_request"
    __table_args__ = (UniqueConstraint("movie_id", "wanted_quality"),)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="movie.id", ondelete="CASCADE"),
    )
    wanted_quality: Mapped[Quality]
    min_quality: Mapped[Quality]

    authorized: Mapped[bool] = mapped_column(default=False)

    requested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )
    authorized_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )

    requested_by: Mapped["User|None"] = relationship(
        foreign_keys=[requested_by_id], uselist=False
    )
    authorized_by: Mapped["User|None"] = relationship(
        foreign_keys=[authorized_by_id], uselist=False
    )
    movie = relationship("Movie", back_populates="movie_requests", uselist=False)
