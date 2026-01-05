import abc

from media_manager.notification.schemas import MessageNotification


class AbstractNotificationServiceProvider(abc.ABC):
    @abc.abstractmethod
    def send_notification(self, message: MessageNotification) -> bool:
        """
        Sends a notification with the given message.

        :param message: The message to send in the notification.
        :return: True if the notification was sent successfully, False otherwise.
        """
        pass
