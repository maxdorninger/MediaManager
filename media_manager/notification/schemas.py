import typing
import uuid
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NotificationId = typing.NewType("NotificationId", UUID)


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: NotificationId = Field(
        default_factory=lambda: NotificationId(uuid.uuid4()),
        description="Unique identifier for the notification",
    )
    read: bool = Field(False, description="Whether the notification has been read")
    message: str = Field(description="The content of the notification")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="The timestamp of the notification"
    )


class MessageNotification(BaseModel):
    """
    Notification type for messages.
    """

    message: str
    title: str
