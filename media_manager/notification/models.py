from uuid import UUID

from sqlalchemy import DateTime, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from media_manager.database import Base


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    message: Mapped[str]
    read: Mapped[bool]
    timestamp = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        # Notifications are always listed newest first and are paginated, so the
        # index matches that order to keep a page from sorting the whole table.
        Index("ix_notification_timestamp_desc", text("timestamp DESC")),
        # Unread notifications are a small fraction of the table, so a partial
        # index keeps the unread query off a full table scan.
        Index(
            "ix_notification_unread_timestamp_desc",
            text("timestamp DESC"),
            postgresql_where=text("read = false"),
            sqlite_where=text("read = 0"),
        ),
    )
