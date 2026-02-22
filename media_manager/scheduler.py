from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import media_manager.database
from media_manager.config import MediaManagerConfig
from media_manager.movies.service import (
    import_all_movie_torrents,
    update_all_movies_metadata,
)
from media_manager.tv.service import (
    import_all_show_torrents,
    update_all_non_ended_shows_metadata,
)


def setup_scheduler(config: MediaManagerConfig) -> BackgroundScheduler:
    from media_manager.database import init_engine

    init_engine(config.database)
    jobstores = {"default": SQLAlchemyJobStore(engine=media_manager.database.engine)}
    scheduler = BackgroundScheduler(jobstores=jobstores)
    every_15_minutes_trigger = CronTrigger(minute="*/15", hour="*")
    weekly_trigger = CronTrigger(
        day_of_week="mon", hour=0, minute=0, jitter=60 * 60 * 24 * 2
    )
    scheduler.add_job(
        import_all_movie_torrents,
        every_15_minutes_trigger,
        id="import_all_movie_torrents",
        replace_existing=True,
    )
    scheduler.add_job(
        import_all_show_torrents,
        every_15_minutes_trigger,
        id="import_all_show_torrents",
        replace_existing=True,
    )
    scheduler.add_job(
        update_all_movies_metadata,
        weekly_trigger,
        id="update_all_movies_metadata",
        replace_existing=True,
    )
    scheduler.add_job(
        update_all_non_ended_shows_metadata,
        weekly_trigger,
        id="update_all_non_ended_shows_metadata",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
