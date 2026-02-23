import asyncio

from taskiq import TaskiqScheduler
from taskiq.cli.scheduler.run import SchedulerLoop
from taskiq_postgresql import PostgresqlBroker
from taskiq_postgresql.scheduler_source import PostgresqlSchedulerSource


def _build_db_connection_string_for_taskiq() -> str:
    from media_manager.config import MediaManagerConfig

    db_config = MediaManagerConfig().database
    return f"postgresql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.dbname}"


broker = PostgresqlBroker(
    dsn=_build_db_connection_string_for_taskiq,
    driver="psycopg",
    run_migrations=True,
)


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
    source = PostgresqlSchedulerSource(
        dsn=_build_db_connection_string_for_taskiq,
        driver="psycopg",
        broker=broker,
        run_migrations=True,
    )
    scheduler = TaskiqScheduler(broker=broker, sources=[source])
    return SchedulerLoop(scheduler)
