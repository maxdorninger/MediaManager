import requests

from media_manager.config import MediaManagerConfig
from media_manager.notification.schemas import MessageNotification
from media_manager.notification.service_providers.abstractNotificationServiceProvider import (
    AbstractNotificationServiceProvider,
)


class PushoverNotificationServiceProvider(AbstractNotificationServiceProvider):
    def __init__(self):
        self.config = MediaManagerConfig().notifications.pushover

    def send_notification(self, message: MessageNotification) -> bool:
        response = requests.post(
            url="https://api.pushover.net/1/messages.json",
            params={
                "token": self.config.api_key,
                "user": self.config.user,
                "message": message.message,
                "title": "MediaManager - " + message.title,
            },
            timeout=60,
        )
        if response.status_code not in range(200, 300):
            return False
        return True
