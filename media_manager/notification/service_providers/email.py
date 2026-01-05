import media_manager.notification.utils
from media_manager.config import MediaManagerConfig
from media_manager.notification.schemas import MessageNotification
from media_manager.notification.service_providers.abstract_notification_service_provider import (
    AbstractNotificationServiceProvider,
)


class EmailNotificationServiceProvider(AbstractNotificationServiceProvider):
    def __init__(self):
        self.config = MediaManagerConfig().notifications.email_notifications

    def send_notification(self, message: MessageNotification) -> bool:
        subject = "MediaManager - " + message.title
        html = f"""\
                <html>
                  <body>
                    <br>
                    {message.message}
                    <br>
                    <br>
                    This is an automated message from MediaManager.</p>
                  </body>
                </html>
                """

        for email in self.config.emails:
            media_manager.notification.utils.send_email(
                subject=subject, html=html, addressee=email
            )

        return True
