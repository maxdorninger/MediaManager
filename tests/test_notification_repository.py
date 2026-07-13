"""Tests for the pagination of the notification repository.

The notification list endpoints used to select the *entire* notification table
(a live instance had ~437k rows), sort it, validate every row and ship the lot
to the browser. The repository now takes a ``limit``/``offset`` page, so these
tests pin the page down: it is bounded, it skips correctly, it stays ordered
newest first, and the unread page never leaks read notifications.

Every assertion is made against a page smaller than the seeded row count, so a
regression to an unbounded query fails the suite rather than passing by luck.
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from media_manager.notification.repository import NotificationRepository
from media_manager.notification.schemas import Notification as NotificationSchema
from media_manager.notification.schemas import NotificationId

# Deliberately larger than any ``limit`` used below, so pagination is exercised.
SEEDED_NOTIFICATIONS = 120

BASE_TIME = datetime(2026, 1, 1, 12, 0, 0)


def build_notification(index: int, *, read: bool) -> NotificationSchema:
    """Build notification ``index``, one minute newer than notification ``index - 1``."""
    return NotificationSchema(
        id=NotificationId(uuid.uuid4()),
        message=f"Notification {index}",
        read=read,
        timestamp=BASE_TIME + timedelta(minutes=index),
    )


@pytest.fixture
async def seeded_notifications(
    session_factory: async_sessionmaker[AsyncSession],
) -> list[NotificationSchema]:
    """Seed alternating read/unread notifications, returned newest first.

    Inserted in oldest-first order so that a query which forgets to order by
    timestamp cannot accidentally return the expected order.
    """
    notifications = [
        build_notification(index, read=index % 2 == 0)
        for index in range(SEEDED_NOTIFICATIONS)
    ]
    async with session_factory() as session:
        repository = NotificationRepository(session)
        for notification in notifications:
            await repository.save_notification(notification)
    return sorted(notifications, key=lambda n: n.timestamp, reverse=True)


def ids(notifications: list[NotificationSchema]) -> list[uuid.UUID]:
    return [notification.id for notification in notifications]


class TestGetAllNotifications:
    async def test_limit_caps_the_number_returned(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            page = await NotificationRepository(session).get_all_notifications(limit=50)

        assert len(page) == 50
        assert ids(page) == ids(seeded_notifications[:50])

    async def test_offset_skips_the_preceding_notifications(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            page = await NotificationRepository(session).get_all_notifications(
                limit=50, offset=50
            )

        assert ids(page) == ids(seeded_notifications[50:100])

    async def test_consecutive_pages_cover_every_notification_exactly_once(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        collected: list[NotificationSchema] = []
        async with session_factory() as session:
            repository = NotificationRepository(session)
            for offset in range(0, SEEDED_NOTIFICATIONS, 50):
                collected += await repository.get_all_notifications(
                    limit=50, offset=offset
                )

        assert ids(collected) == ids(seeded_notifications)

    async def test_offset_past_the_end_returns_an_empty_page(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            page = await NotificationRepository(session).get_all_notifications(
                limit=50, offset=SEEDED_NOTIFICATIONS
            )

        assert page == []

    async def test_page_is_ordered_by_timestamp_descending(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            page = await NotificationRepository(session).get_all_notifications(limit=50)

        timestamps = [notification.timestamp for notification in page]
        assert timestamps == sorted(timestamps, reverse=True)
        # The newest seeded notification has to be the first row of the first page.
        assert page[0].timestamp == seeded_notifications[0].timestamp

    async def test_read_filter_returns_only_read_notifications(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        expected = [n for n in seeded_notifications if n.read]
        async with session_factory() as session:
            page = await NotificationRepository(session).get_all_notifications(
                limit=20, offset=10, read=True
            )

        assert all(notification.read for notification in page)
        assert ids(page) == ids(expected[10:30])


class TestGetUnreadNotifications:
    async def test_returns_only_unread_notifications(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            page = await NotificationRepository(session).get_unread_notifications(
                limit=50
            )

        assert page != []
        assert not any(notification.read for notification in page)

    async def test_limit_caps_the_number_returned(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        unread = [n for n in seeded_notifications if not n.read]
        assert len(unread) > 20, "the seed must exceed the limit under test"

        async with session_factory() as session:
            page = await NotificationRepository(session).get_unread_notifications(
                limit=20
            )

        assert len(page) == 20
        assert ids(page) == ids(unread[:20])

    async def test_offset_skips_the_preceding_unread_notifications(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        unread = [n for n in seeded_notifications if not n.read]
        async with session_factory() as session:
            page = await NotificationRepository(session).get_unread_notifications(
                limit=20, offset=20
            )

        assert ids(page) == ids(unread[20:40])

    async def test_page_is_ordered_by_timestamp_descending(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            page = await NotificationRepository(session).get_unread_notifications(
                limit=50
            )

        timestamps = [notification.timestamp for notification in page]
        assert timestamps == sorted(timestamps, reverse=True)


class TestMarkAllNotificationsAsRead:
    async def test_marks_every_unread_notification_read(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        """A single statement has to reach past the page the client holds."""
        async with session_factory() as session:
            repository = NotificationRepository(session)
            await repository.mark_all_notifications_as_read()
            await session.commit()

        async with session_factory() as session:
            repository = NotificationRepository(session)
            unread = await repository.count_notifications(read=False)
            read = await repository.count_notifications(read=True)

        assert unread == 0
        assert read == SEEDED_NOTIFICATIONS


class TestCountNotifications:
    async def test_counts_every_notification_by_default(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            total = await NotificationRepository(session).count_notifications()

        assert total == SEEDED_NOTIFICATIONS

    async def test_counts_unread_and_read_separately(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        async with session_factory() as session:
            repository = NotificationRepository(session)
            unread = await repository.count_notifications(read=False)
            read = await repository.count_notifications(read=True)

        assert unread == len([n for n in seeded_notifications if not n.read])
        assert read == len([n for n in seeded_notifications if n.read])
        assert unread + read == SEEDED_NOTIFICATIONS

    async def test_count_is_independent_of_the_page_size(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        seeded_notifications: list[NotificationSchema],
    ) -> None:
        """The UI paginates on this count, so it must describe the whole table."""
        async with session_factory() as session:
            repository = NotificationRepository(session)
            page = await repository.get_all_notifications(limit=10)
            total = await repository.count_notifications()

        assert len(page) == 10
        assert total == SEEDED_NOTIFICATIONS
