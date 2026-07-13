from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from media_manager.auth.users import current_active_user
from media_manager.notification.dependencies import notification_service_dep
from media_manager.notification.schemas import Notification, NotificationId

router = APIRouter()

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

TOTAL_COUNT_HEADER = "X-Total-Count"

limit_dep = Annotated[
    int,
    Query(
        ge=1, le=MAX_PAGE_SIZE, description="Maximum number of notifications to return"
    ),
]
offset_dep = Annotated[int, Query(ge=0, description="Number of notifications to skip")]


# --------------------------------
# GET NOTIFICATIONS
# --------------------------------


@router.get(
    "",
    dependencies=[Depends(current_active_user)],
)
async def get_all_notifications(
    notification_service: notification_service_dep,
    response: Response,
    limit: limit_dep = DEFAULT_PAGE_SIZE,
    offset: offset_dep = 0,
    read: Annotated[
        bool | None,
        Query(description="Only return read (true) or unread (false) notifications"),
    ] = None,
) -> list[Notification]:
    """
    Get a page of notifications, newest first.

    The total number of matching notifications is returned in the
    `X-Total-Count` response header.
    """
    total = await notification_service.count_notifications(read=read)
    response.headers[TOTAL_COUNT_HEADER] = str(total)
    return await notification_service.get_all_notifications(
        limit=limit, offset=offset, read=read
    )


@router.get(
    "/unread",
    dependencies=[Depends(current_active_user)],
)
async def get_unread_notifications(
    notification_service: notification_service_dep,
    response: Response,
    limit: limit_dep = DEFAULT_PAGE_SIZE,
    offset: offset_dep = 0,
) -> list[Notification]:
    """
    Get a page of unread notifications, newest first.

    The total number of unread notifications is returned in the `X-Total-Count`
    response header.
    """
    total = await notification_service.count_notifications(read=False)
    response.headers[TOTAL_COUNT_HEADER] = str(total)
    return await notification_service.get_unread_notifications(
        limit=limit, offset=offset
    )


@router.get(
    "/{notification_id}",
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
async def get_notification(
    notification_id: NotificationId, notification_service: notification_service_dep
) -> Notification:
    """
    Get a specific notification by ID.
    """
    return await notification_service.get_notification(nid=notification_id)


# --------------------------------
# MANAGE NOTIFICATIONS
# --------------------------------


@router.patch(
    "/read",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
)
async def mark_all_notifications_as_read(
    notification_service: notification_service_dep,
) -> None:
    """
    Mark every unread notification as read.

    The client only holds a page of notifications, so it cannot mark them all
    read by iterating over the ones it has.
    """
    await notification_service.mark_all_notifications_as_read()


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
async def mark_notification_as_read(
    notification_id: NotificationId, notification_service: notification_service_dep
) -> None:
    """
    Mark a notification as read.
    """
    await notification_service.mark_notification_as_read(nid=notification_id)


@router.patch(
    "/{notification_id}/unread",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
async def mark_notification_as_unread(
    notification_id: NotificationId, notification_service: notification_service_dep
) -> None:
    """
    Mark a notification as unread.
    """
    await notification_service.mark_notification_as_unread(nid=notification_id)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Notification not found"},
    },
)
async def delete_notification(
    notification_id: NotificationId, notification_service: notification_service_dep
) -> None:
    """
    Delete a notification.
    """
    await notification_service.delete_notification(nid=notification_id)
