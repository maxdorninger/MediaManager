import logging

from sqlalchemy import delete, select, update
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.notification.models import Notification
from media_manager.notification.schemas import (
    Notification as NotificationSchema,
)
from media_manager.notification.schemas import (
    NotificationId,
)

log = logging.getLogger(__name__)


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_notification(self, nid: NotificationId) -> NotificationSchema:
        result = self.db.get(Notification, nid)

        if not result:
            msg = f"Notification with id {nid} not found."
            raise NotFoundError(msg)

        return NotificationSchema.model_validate(result)

    def get_unread_notifications(self) -> list[NotificationSchema]:
        try:
            stmt = (
                select(Notification)
                .where(Notification.read == False)  # noqa: E712
                .order_by(Notification.timestamp.desc())
            )
            results = self.db.execute(stmt).scalars().all()
            return [
                NotificationSchema.model_validate(notification)
                for notification in results
            ]
        except SQLAlchemyError:
            log.exception("Database error while retrieving unread notifications")
            raise

    def get_all_notifications(self) -> list[NotificationSchema]:
        try:
            stmt = select(Notification).order_by(Notification.timestamp.desc())
            results = self.db.execute(stmt).scalars().all()
            return [
                NotificationSchema.model_validate(notification)
                for notification in results
            ]
        except SQLAlchemyError:
            log.exception("Database error while retrieving notifications")
            raise

    def save_notification(self, notification: NotificationSchema) -> None:
        try:
            self.db.add(
                Notification(
                    id=notification.id,
                    read=notification.read,
                    timestamp=notification.timestamp,
                    message=notification.message,
                )
            )
            self.db.commit()
        except IntegrityError:
            log.exception("Could not save notification")
            msg = f"Notification with id {notification.id} already exists."
            raise ConflictError(msg) from None
        return

    def mark_notification_as_read(self, nid: NotificationId) -> None:
        stmt = update(Notification).where(Notification.id == nid).values(read=True)
        self.db.execute(stmt)
        return

    def mark_notification_as_unread(self, nid: NotificationId) -> None:
        stmt = update(Notification).where(Notification.id == nid).values(read=False)
        self.db.execute(stmt)
        return

    def delete_notification(self, nid: NotificationId) -> None:
        stmt = delete(Notification).where(Notification.id == nid)
        result = self.db.execute(stmt)
        if result.rowcount == 0:
            msg = f"Notification with id {nid} not found."
            raise NotFoundError(msg)
        self.db.commit()
        return
