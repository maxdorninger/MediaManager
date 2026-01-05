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
    def __init__(self, db: Session):
        self.db = db

    def get_notification(self, id: NotificationId) -> NotificationSchema:
        result = self.db.get(Notification, id)

        if not result:
            msg = f"Notification with id {id} not found."
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
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving unread notifications: {e}")
            raise

    def get_all_notifications(self) -> list[NotificationSchema]:
        try:
            stmt = select(Notification).order_by(Notification.timestamp.desc())
            results = self.db.execute(stmt).scalars().all()
            return [
                NotificationSchema.model_validate(notification)
                for notification in results
            ]
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving notifications: {e}")
            raise

    def save_notification(self, notification: NotificationSchema):
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
        except IntegrityError as e:
            log.error(f"Could not save notification, Error: {e}")
            msg = f"Notification with id {notification.id} already exists."
            raise ConflictError(msg) from None
        return

    def mark_notification_as_read(self, id: NotificationId) -> None:
        stmt = update(Notification).where(Notification.id == id).values(read=True)
        self.db.execute(stmt)
        return

    def mark_notification_as_unread(self, id: NotificationId) -> None:
        stmt = update(Notification).where(Notification.id == id).values(read=False)
        self.db.execute(stmt)
        return

    def delete_notification(self, id: NotificationId) -> None:
        stmt = delete(Notification).where(Notification.id == id)
        result = self.db.execute(stmt)
        if result.rowcount == 0:
            msg = f"Notification with id {id} not found."
            raise NotFoundError(msg)
        self.db.commit()
        return
