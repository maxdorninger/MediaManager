import asyncio

from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq.cli.scheduler.run import SchedulerLoop
from taskiq.schedule_sources import LabelScheduleSource

broker = InMemoryBroker()


@broker.task(schedule=[{"cron": "*/15 * * * *"}])
async def import_all_movie_torrents_task() -> None:
    from media_manager.movies.service import import_all_movie_torrents

    await asyncio.to_thread(import_all_movie_torrents)


@broker.task(schedule=[{"cron": "*/15 * * * *"}])
async def import_all_show_torrents_task() -> None:
    from media_manager.tv.service import import_all_show_torrents

    await asyncio.to_thread(import_all_show_torrents)


@broker.task(schedule=[{"cron": "0 0 * * 1"}])
async def update_all_movies_metadata_task() -> None:
    from media_manager.movies.service import update_all_movies_metadata

    await asyncio.to_thread(update_all_movies_metadata)


@broker.task(schedule=[{"cron": "0 0 * * 1"}])
async def update_all_non_ended_shows_metadata_task() -> None:
    from media_manager.tv.service import update_all_non_ended_shows_metadata

    await asyncio.to_thread(update_all_non_ended_shows_metadata)


def build_scheduler_loop() -> SchedulerLoop:
    scheduler = TaskiqScheduler(
        broker=broker,
        sources=[LabelScheduleSource(broker)],
    )
    return SchedulerLoop(scheduler)
