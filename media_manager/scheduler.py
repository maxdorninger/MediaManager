import asyncio
import logging
from urllib.parse import quote

import taskiq_fastapi
from taskiq import TaskiqDepends, TaskiqScheduler
from taskiq.cli.scheduler.run import SchedulerLoop
from taskiq_postgresql import PostgresqlBroker
from taskiq_postgresql.scheduler_source import PostgresqlSchedulerSource

from media_manager.movies.dependencies import get_movie_service
from media_manager.movies.service import MovieService
from media_manager.tv.dependencies import get_tv_service
from media_manager.tv.service import TvService


def _build_db_connection_string_for_taskiq() -> str:
    from media_manager.config import MediaManagerConfig

    db_config = MediaManagerConfig().database
    user = quote(db_config.user, safe="")
    password = quote(db_config.password, safe="")
    dbname = quote(db_config.dbname, safe="")
    host = quote(str(db_config.host), safe="")
    port = quote(str(db_config.port), safe="")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


broker = PostgresqlBroker(
    dsn=_build_db_connection_string_for_taskiq,
    driver="psycopg",
    run_migrations=True,
)

# Register FastAPI app with the broker so worker processes can resolve FastAPI
# dependencies. Using a string reference avoids circular imports.
taskiq_fastapi.init(broker, "media_manager.main:app")

log = logging.getLogger(__name__)


@broker.task
async def import_all_movie_torrents_task(
    movie_service: MovieService = TaskiqDepends(get_movie_service),
) -> None:
    log.info("Importing all Movie torrents")
    await asyncio.to_thread(movie_service.import_all_torrents)


@broker.task
async def import_all_show_torrents_task(
    tv_service: TvService = TaskiqDepends(get_tv_service),
) -> None:
    log.info("Importing all Show torrents")
    await asyncio.to_thread(tv_service.import_all_torrents)


@broker.task
async def update_all_movies_metadata_task(
    movie_service: MovieService = TaskiqDepends(get_movie_service),
) -> None:
    await asyncio.to_thread(movie_service.update_all_metadata)


@broker.task
async def update_all_non_ended_shows_metadata_task(
    tv_service: TvService = TaskiqDepends(get_tv_service),
) -> None:
    await asyncio.to_thread(tv_service.update_all_non_ended_shows_metadata)


# Maps each task to its cron schedule so PostgresqlSchedulerSource can seed
# the taskiq_schedulers table on first startup.
_STARTUP_SCHEDULES: dict = {
    import_all_movie_torrents_task.task_name: [{"cron": "*/2 * * * *"}],
    import_all_show_torrents_task.task_name: [{"cron": "*/2 * * * *"}],
    update_all_movies_metadata_task.task_name: [{"cron": "0 0 * * 1"}],
    update_all_non_ended_shows_metadata_task.task_name: [{"cron": "0 0 * * 1"}],
}


def build_scheduler_loop() -> SchedulerLoop:
    source = PostgresqlSchedulerSource(
        dsn=_build_db_connection_string_for_taskiq,
        driver="psycopg",
        broker=broker,
        run_migrations=True,
        startup_schedule=_STARTUP_SCHEDULES,
    )
    scheduler = TaskiqScheduler(broker=broker, sources=[source])
    return SchedulerLoop(scheduler)
