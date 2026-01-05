"""
Notification Manager - Orchestrates sending notifications through all configured service providers
"""

import logging
from typing import List

from media_manager.config import MediaManagerConfig
from media_manager.notification.schemas import MessageNotification
from media_manager.notification.service_providers.abstract_notification_service_provider import (
    AbstractNotificationServiceProvider,
)
from media_manager.notification.service_providers.email import (
    EmailNotificationServiceProvider,
)
from media_manager.notification.service_providers.gotify import (
    GotifyNotificationServiceProvider,
)
from media_manager.notification.service_providers.ntfy import (
    NtfyNotificationServiceProvider,
)
from media_manager.notification.service_providers.pushover import (
    PushoverNotificationServiceProvider,
)

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages and orchestrates notifications across all configured service providers.
    """

    def __init__(self):
        self.config = MediaManagerConfig().notifications
        self.providers: List[AbstractNotificationServiceProvider] = []
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        # Email provider
        if self.config.email_notifications.enabled:
            try:
                self.providers.append(EmailNotificationServiceProvider())
                logger.info("Email notification provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Email provider: {e}")

        # Gotify provider
        if self.config.gotify.enabled:
            try:
                self.providers.append(GotifyNotificationServiceProvider())
                logger.info("Gotify notification provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gotify provider: {e}")

        # Ntfy provider
        if self.config.ntfy.enabled:
            try:
                self.providers.append(NtfyNotificationServiceProvider())
                logger.info("Ntfy notification provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Ntfy provider: {e}")

        # Pushover provider
        if self.config.pushover.enabled:
            try:
                self.providers.append(PushoverNotificationServiceProvider())
                logger.info("Pushover notification provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Pushover provider: {e}")

        logger.info(f"Initialized {len(self.providers)} notification providers")

    def send_notification(self, title: str, message: str) -> None:
        if not self.providers:
            logger.warning("No notification providers configured")

        notification = MessageNotification(title=title, message=message)

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                success = provider.send_notification(notification)
                if success:
                    logger.info(f"Notification sent successfully via {provider_name}")
                else:
                    logger.warning(f"Failed to send notification via {provider_name}")

            except Exception as e:
                logger.error(f"Error sending notification via {provider_name}: {e}")

    def get_configured_providers(self) -> List[str]:
        return [provider.__class__.__name__ for provider in self.providers]

    def is_configured(self) -> bool:
        return len(self.providers) > 0


notification_manager = NotificationManager()
