from uuid import UUID

from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import BigInteger

from media_manager.database import Base
from media_manager.torrent.schemas import Quality


class IndexerQueryResult(Base):
    __tablename__ = "indexer_query_result"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    download_url: Mapped[str]
    seeders: Mapped[int]
    flags = mapped_column(ARRAY(String))
    quality: Mapped[Quality]
    season = mapped_column(ARRAY(Integer))
    size = mapped_column(BigInteger)
    usenet: Mapped[bool]
    age: Mapped[int]
    score: Mapped[int] = mapped_column(default=0)
    indexer: Mapped[str | None]
