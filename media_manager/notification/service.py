from media_manager.notification.manager import notification_manager
from media_manager.notification.repository import NotificationRepository
from media_manager.notification.schemas import Notification, NotificationId


class NotificationService:
    def __init__(
        self,
        notification_repository: NotificationRepository,
    ) -> None:
        self.notification_repository = notification_repository
        self.notification_manager = notification_manager

    async def get_notification(self, nid: NotificationId) -> Notification:
        return await self.notification_repository.get_notification(nid=nid)

    async def get_unread_notifications(
        self, limit: int, offset: int = 0
    ) -> list[Notification]:
        return await self.notification_repository.get_unread_notifications(
            limit=limit, offset=offset
        )

    async def get_all_notifications(
        self, limit: int, offset: int = 0, read: bool | None = None
    ) -> list[Notification]:
        return await self.notification_repository.get_all_notifications(
            limit=limit, offset=offset, read=read
        )

    async def count_notifications(self, read: bool | None = None) -> int:
        return await self.notification_repository.count_notifications(read=read)

    async def save_notification(self, notification: Notification) -> None:
        return await self.notification_repository.save_notification(notification)

    async def mark_notification_as_read(self, nid: NotificationId) -> None:
        return await self.notification_repository.mark_notification_as_read(nid=nid)

    async def mark_notification_as_unread(self, nid: NotificationId) -> None:
        return await self.notification_repository.mark_notification_as_unread(nid=nid)

    async def mark_all_notifications_as_read(self) -> None:
        return await self.notification_repository.mark_all_notifications_as_read()

    async def delete_notification(self, nid: NotificationId) -> None:
        return await self.notification_repository.delete_notification(nid=nid)

    async def send_notification_to_all_providers(self, title: str, message: str) -> None:
        await self.notification_manager.send_notification(title, message)

        internal_notification = Notification(message=f"{title}: {message}", read=False)
        await self.save_notification(internal_notification)
        return
