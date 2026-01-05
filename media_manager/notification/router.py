from fastapi import APIRouter, Depends, status

from media_manager.auth.users import current_active_user
from media_manager.notification.dependencies import notification_service_dep
from media_manager.notification.schemas import Notification, NotificationId

router = APIRouter()


# --------------------------------
# GET NOTIFICATIONS
# --------------------------------


@router.get(
    "",
    dependencies=[Depends(current_active_user)],
)
def get_all_notifications(
    notification_service: notification_service_dep,
) -> list[Notification]:
    """
    Get all notifications.
    """
    return notification_service.get_all_notifications()


@router.get(
    "/unread",
    dependencies=[Depends(current_active_user)],
)
def get_unread_notifications(
    notification_service: notification_service_dep,
) -> list[Notification]:
    """
    Get all unread notifications.
    """
    return notification_service.get_unread_notifications()


@router.get(
    "/{notification_id}",
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
def get_notification(
    notification_id: NotificationId, notification_service: notification_service_dep
) -> Notification:
    """
    Get a specific notification by ID.
    """
    return notification_service.get_notification(id=notification_id)


# --------------------------------
# MANAGE NOTIFICATIONS
# --------------------------------


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
def mark_notification_as_read(
    notification_id: NotificationId, notification_service: notification_service_dep
):
    """
    Mark a notification as read.
    """
    notification_service.mark_notification_as_read(id=notification_id)


@router.patch(
    "/{notification_id}/unread",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
def mark_notification_as_unread(
    notification_id: NotificationId, notification_service: notification_service_dep
):
    """
    Mark a notification as unread.
    """
    notification_service.mark_notification_as_unread(id=notification_id)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
def delete_notification(
    notification_id: NotificationId, notification_service: notification_service_dep
):
    """
    Delete a notification.
    """
    notification_service.delete_notification(id=notification_id)
