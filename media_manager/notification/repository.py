import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.sql.expression import false, true

from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.notification.models import Notification
from media_manager.notification.schemas import (
    Notification as NotificationSchema,
)
from media_manager.notification.schemas import (
    NotificationId,
)

log = logging.getLogger(__name__)


def _filtered_by_read(stmt: Select, read: bool | None) -> Select:
    if read is None:
        return stmt
    return stmt.where(Notification.read == (true() if read else false()))


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_notification(self, nid: NotificationId) -> NotificationSchema:
        result = await self.db.get(Notification, nid)

        if not result:
            msg = f"Notification with id {nid} not found."
            raise NotFoundError(msg)

        return NotificationSchema.model_validate(result)

    async def get_unread_notifications(
        self, limit: int, offset: int = 0
    ) -> list[NotificationSchema]:
        try:
            stmt = (
                _filtered_by_read(select(Notification), read=False)
                .order_by(Notification.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            results = (await self.db.execute(stmt)).scalars().all()
            return [
                NotificationSchema.model_validate(notification)
                for notification in results
            ]
        except SQLAlchemyError:
            log.exception("Database error while retrieving unread notifications")
            raise

    async def get_all_notifications(
        self, limit: int, offset: int = 0, read: bool | None = None
    ) -> list[NotificationSchema]:
        """Return one page of notifications, newest first.

        ``read`` optionally restricts the page to read or unread notifications;
        ``None`` returns both.
        """
        try:
            stmt = (
                _filtered_by_read(select(Notification), read=read)
                .order_by(Notification.timestamp.desc())
                .limit(limit)
                .offset(offset)
            )
            results = (await self.db.execute(stmt)).scalars().all()
            return [
                NotificationSchema.model_validate(notification)
                for notification in results
            ]
        except SQLAlchemyError:
            log.exception("Database error while retrieving notifications")
            raise

    async def count_notifications(self, read: bool | None = None) -> int:
        """Count the notifications a matching page would be taken from."""
        try:
            stmt = _filtered_by_read(
                select(func.count()).select_from(Notification), read=read
            )
            return (await self.db.execute(stmt)).scalar_one()
        except SQLAlchemyError:
            log.exception("Database error while counting notifications")
            raise

    async def save_notification(self, notification: NotificationSchema) -> None:
        try:
            self.db.add(
                Notification(
                    id=notification.id,
                    read=notification.read,
                    timestamp=notification.timestamp,
                    message=notification.message,
                )
            )
            await self.db.commit()
        except IntegrityError:
            # AsyncSession leaves the txn in invalid state on IntegrityError;
            # without rollback the request-end commit raises PendingRollbackError.
            await self.db.rollback()
            log.exception("Could not save notification")
            msg = f"Notification with id {notification.id} already exists."
            raise ConflictError(msg) from None
        return

    async def mark_notification_as_read(self, nid: NotificationId) -> None:
        stmt = update(Notification).where(Notification.id == nid).values(read=True)
        await self.db.execute(stmt)
        return

    async def mark_notification_as_unread(self, nid: NotificationId) -> None:
        stmt = update(Notification).where(Notification.id == nid).values(read=False)
        await self.db.execute(stmt)
        return

    async def mark_all_notifications_as_read(self) -> None:
        """Mark every unread notification as read in a single statement.

        The UI only holds a page of notifications now, so it can no longer mark
        them all read by looping over the ones it has.
        """
        stmt = (
            update(Notification).where(Notification.read == false()).values(read=True)
        )
        await self.db.execute(stmt)
        return

    async def delete_notification(self, nid: NotificationId) -> None:
        stmt = delete(Notification).where(Notification.id == nid)
        result = await self.db.execute(stmt)
        if result.rowcount == 0:
            msg = f"Notification with id {nid} not found."
            raise NotFoundError(msg)
        await self.db.commit()
        return
