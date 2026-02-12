from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.database import Base
from media_manager.torrent.schemas import Quality, TorrentStatus


class Torrent(Base):
    __tablename__ = "torrent"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    status: Mapped[TorrentStatus]
    title: Mapped[str]
    quality: Mapped[Quality]
    imported: Mapped[bool]
    hash: Mapped[str]
    usenet: Mapped[bool]

    episode_files = relationship("EpisodeFile", back_populates="torrent")
    movie_files = relationship("MovieFile", back_populates="torrent")
