from uuid import UUID

from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.auth.db import User
from media_manager.database import Base
from media_manager.torrent.models import Quality


class Author(Base):
    __tablename__ = "book_author"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[str]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str]
    library: Mapped[str] = mapped_column(default="")

    books: Mapped[list["Book"]] = relationship(
        back_populates="author", cascade="all, delete"
    )


class Book(Base):
    __tablename__ = "book"
    __table_args__ = (UniqueConstraint("author_id", "external_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="book_author.id", ondelete="CASCADE"),
    )
    external_id: Mapped[str]
    name: Mapped[str]
    year: Mapped[int | None]
    format: Mapped[str] = mapped_column(default="ebook")
    isbn: Mapped[str | None] = mapped_column(default=None)
    publisher: Mapped[str | None] = mapped_column(default=None)
    page_count: Mapped[int | None] = mapped_column(default=None)

    author: Mapped["Author"] = relationship(back_populates="books")

    book_files = relationship(
        "BookFile", back_populates="book", cascade="all, delete"
    )
    book_requests = relationship(
        "BookRequest", back_populates="book", cascade="all, delete"
    )


class BookFile(Base):
    __tablename__ = "book_file"
    __table_args__ = (PrimaryKeyConstraint("book_id", "file_path_suffix"),)

    book_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="book.id", ondelete="CASCADE"),
    )
    torrent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="torrent.id", ondelete="SET NULL"),
    )
    file_path_suffix: Mapped[str]
    quality: Mapped[Quality]

    torrent = relationship("Torrent", back_populates="book_files", uselist=False)
    book = relationship("Book", back_populates="book_files", uselist=False)


class BookRequest(Base):
    __tablename__ = "book_request"
    __table_args__ = (UniqueConstraint("book_id", "wanted_quality"),)

    id: Mapped[UUID] = mapped_column(primary_key=True)
    book_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="book.id", ondelete="CASCADE"),
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
    book = relationship("Book", back_populates="book_requests", uselist=False)
