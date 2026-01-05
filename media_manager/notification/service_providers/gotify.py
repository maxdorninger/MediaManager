import requests

from media_manager.config import MediaManagerConfig
from media_manager.notification.schemas import MessageNotification
from media_manager.notification.service_providers.abstract_notification_service_provider import (
    AbstractNotificationServiceProvider,
)


class GotifyNotificationServiceProvider(AbstractNotificationServiceProvider):
    """
    Gotify Notification Service Provider
    """

    def __init__(self):
        self.config = MediaManagerConfig().notifications.gotify

    def send_notification(self, message: MessageNotification) -> bool:
        response = requests.post(
            url=f"{self.config.url}/message?token={self.config.api_key}",
            json={
                "message": message.message,
                "title": message.title,
            },
            timeout=60,
        )
        if response.status_code not in range(200, 300):
            return False
        return True
