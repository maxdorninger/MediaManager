from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.common.models import MediaFileMixin, MediaMixin
from media_manager.database import Base


class Show(Base, MediaMixin):
    __tablename__ = "show"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)

    ended: Mapped[bool] = mapped_column(default=False)
    continuous_download: Mapped[bool] = mapped_column(default=False)

    seasons: Mapped[list["Season"]] = relationship(
        back_populates="show", cascade="all, delete"
    )


class Season(Base):
    __tablename__ = "season"
    __table_args__ = (UniqueConstraint("show_id", "number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    show_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="show.id", ondelete="CASCADE"),
    )
    number: Mapped[int]
    external_id: Mapped[int]
    name: Mapped[str]
    overview: Mapped[str]

    show: Mapped["Show"] = relationship(back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="season", cascade="all, delete"
    )


class Episode(Base):
    __tablename__ = "episode"
    __table_args__ = (UniqueConstraint("season_id", "number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    season_id: Mapped[UUID] = mapped_column(
        ForeignKey("season.id", ondelete="CASCADE"),
    )
    number: Mapped[int]
    external_id: Mapped[int]
    title: Mapped[str]
    overview: Mapped[str | None] = mapped_column(nullable=True)

    season: Mapped["Season"] = relationship(back_populates="episodes")
    episode_files = relationship(
        "EpisodeFile", back_populates="episode", cascade="all, delete"
    )


class EpisodeFile(Base, MediaFileMixin):
    __tablename__ = "episode_file"
    __table_args__ = (PrimaryKeyConstraint("episode_id", "file_path_suffix"),)
    episode_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="episode.id", ondelete="CASCADE"),
    )

    torrent = relationship("Torrent", back_populates="episode_files", uselist=False)
    episode = relationship("Episode", back_populates="episode_files", uselist=False)
