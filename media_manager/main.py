import logging
import os
import sys
from logging.config import dictConfig
from pathlib import Path

from psycopg.errors import UniqueViolation
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy.exc import IntegrityError

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s(): %(message)s"
        },
        "json": {
            "()": JsonFormatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "./log.txt",
            "maxBytes": 10485760,
            "backupCount": 5,
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": "DEBUG"},
        "uvicorn.access": {"handlers": ["console", "file"], "level": "DEBUG"},
        "fastapi": {"handlers": ["console", "file"], "level": "DEBUG"},
    },
}
dictConfig(LOGGING_CONFIG)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s(): %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

from media_manager.database import init_db  # noqa: E402
from media_manager.config import AllEncompassingConfig  # noqa: E402
from media_manager.plugins.manager import plugin_manager  # noqa: E402
import media_manager.torrent.router as torrent_router  # noqa: E402
import media_manager.movies.router as movies_router  # noqa: E402
import media_manager.tv.router as tv_router  # noqa: E402
from media_manager.tv.service import (  # noqa: E402
    auto_download_all_approved_season_requests,
    import_all_show_torrents,
    update_all_non_ended_shows_metadata,
)
from media_manager.movies.service import (  # noqa: E402
    import_all_movie_torrents,
    update_all_movies_metadata,
    auto_download_all_approved_movie_requests,
)
from media_manager.notification.router import router as notification_router  # noqa: E402
import uvicorn  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from media_manager.auth.users import openid_client  # noqa: E402
from media_manager.auth.users import SECRET as AUTH_USERS_SECRET  # noqa: E402
from media_manager.auth.router import users_router as custom_users_router  # noqa: E402
from media_manager.auth.router import auth_metadata_router  # noqa: E402
from media_manager.auth.schemas import UserCreate, UserRead, UserUpdate  # noqa: E402
from media_manager.auth.oauth import get_oauth_router  # noqa: E402

from media_manager.auth.users import (  # noqa: E402
    bearer_auth_backend,
    fastapi_users,
    cookie_auth_backend,
    openid_cookie_auth_backend,
    create_default_admin_user,
)
from media_manager.exceptions import (  # noqa: E402
    NotFoundError,
    not_found_error_exception_handler,
    MediaAlreadyExists,
    media_already_exists_exception_handler,
    InvalidConfigError,
    invalid_config_error_exception_handler,
    sqlalchemy_integrity_error_handler,
)

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore  # noqa: E402
from starlette.responses import FileResponse, RedirectResponse  # noqa: E402

import media_manager.database  # noqa: E402
import shutil  # noqa: E402
from fastapi import FastAPI, APIRouter  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware  # noqa: E402
from starlette.responses import Response  # noqa: E402
from datetime import datetime  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from apscheduler.schedulers.background import BackgroundScheduler  # noqa: E402
from apscheduler.triggers.cron import CronTrigger  # noqa: E402

init_db()
log.info("Database initialized")
config = AllEncompassingConfig()

if config.misc.development:
    log.warning("Development Mode activated!")
else:
    log.info("Development Mode not activated!")

# Initialize plugin system
log.info("Initializing plugin system...")
plugin_configs = {}
for plugin_name in config.media_plugins.get_enabled_plugins():
    plugin_configs[plugin_name] = config.media_plugins.get_plugin_config(plugin_name)

plugin_manager.load_all_plugins(plugin_configs)
log.info(f"Plugin system initialized with {len(plugin_manager.get_all_plugins())} plugins")


def hourly_tasks():
    log.info(f"Hourly tasks are running at {datetime.now()}")
    # Run plugin-specific auto download and import tasks
    for plugin_name, plugin in plugin_manager.get_all_plugins().items():
        try:
            log.info(f"Running hourly tasks for {plugin_name}")
            # Get service instances with proper dependencies
            from media_manager.database import get_session
            session = next(get_session())
            service = plugin.get_service(session=session)
            service.auto_download_approved_requests()
            service.import_downloaded_files()
        except Exception as e:
            log.error(f"Error running hourly tasks for plugin {plugin_name}: {e}")


def weekly_tasks():
    log.info(f"Weekly tasks are running at {datetime.now()}")
    # Run plugin-specific metadata update tasks
    for plugin_name, plugin in plugin_manager.get_all_plugins().items():
        try:
            log.info(f"Running weekly metadata updates for {plugin_name}")
            # Note: This would need to be implemented per plugin
            # For now, fall back to existing functions for TV/Movies
            if plugin_name == "tv":
                update_all_non_ended_shows_metadata()
            elif plugin_name == "movies":
                update_all_movies_metadata()
        except Exception as e:
            log.error(f"Error running weekly tasks for plugin {plugin_name}: {e}")


jobstores = {"default": SQLAlchemyJobStore(engine=media_manager.database.engine)}

scheduler = BackgroundScheduler(jobstores=jobstores)
every_15_minutes_trigger = CronTrigger(minute="*/15", hour="*")
daily_trigger = CronTrigger(hour=0, minute=0, jitter=60 * 60 * 24 * 2)
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
    auto_download_all_approved_season_requests,
    daily_trigger,
    id="auto_download_all_approved_season_requests",
    replace_existing=True,
)
scheduler.add_job(
    auto_download_all_approved_movie_requests,
    daily_trigger,
    id="auto_download_all_approved_movie_requests",
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create default admin user if needed
    await create_default_admin_user()
    yield
    # Shutdown
    log.info("Shutting down application...")
    scheduler.shutdown()
    plugin_manager.shutdown_all_plugins()
    log.info("Application shutdown complete")


BASE_PATH = os.getenv("BASE_PATH", "")
FRONTEND_FILES_DIR = os.getenv("FRONTEND_FILES_DIR")


app = FastAPI(lifespan=lifespan, root_path=BASE_PATH)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

origins = config.misc.cors_urls
log.info("CORS URLs activated for following origins:")
for origin in origins:
    log.info(f" - {origin}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_app = APIRouter(prefix="/api/v1")

# ----------------------------
# Hello World Router
# ----------------------------


@api_app.get("/health")
async def hello_world() -> dict:
    """
    A simple endpoint to check if the API is running.
    """
    return {"message": "Hello World!", "version": os.getenv("PUBLIC_VERSION")}


@api_app.get("/plugins")
async def get_plugins() -> dict:
    """
    Get information about all loaded plugins.
    """
    plugins = {}
    for plugin_name, plugin in plugin_manager.get_all_plugins().items():
        plugins[plugin_name] = {
            "info": plugin.plugin_info.model_dump(),
            "enabled": True
        }
    
    return {
        "plugins": plugins,
        "total_count": len(plugins)
    }


# ----------------------------
# Standard Auth Routers
# ----------------------------

api_app.include_router(
    fastapi_users.get_auth_router(bearer_auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
api_app.include_router(
    fastapi_users.get_auth_router(cookie_auth_backend),
    prefix="/auth/cookie",
    tags=["auth"],
)
api_app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
api_app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
api_app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# ----------------------------
# User Management Routers
# ----------------------------

api_app.include_router(custom_users_router, tags=["users"])
api_app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# ----------------------------
# OpenID Connect Routers
# ----------------------------

api_app.include_router(auth_metadata_router, tags=["openid"])

if openid_client is not None:
    api_app.include_router(
        get_oauth_router(
            oauth_client=openid_client,
            backend=openid_cookie_auth_backend,
            get_user_manager=fastapi_users.get_user_manager,
            state_secret=AUTH_USERS_SECRET,
            associate_by_email=True,
            is_verified_by_default=True,
        ),
        prefix=f"/auth/cookie/{openid_client.name}",
        tags=["openid"],
    )

# Include plugin routers
for plugin_name, router in plugin_manager.get_all_routers():
    plugin_info = plugin_manager.get_plugin(plugin_name).plugin_info
    api_app.include_router(
        router, 
        prefix=f"/{plugin_name}", 
        tags=[plugin_info.media_type]
    )
    log.info(f"Registered router for plugin: {plugin_info.display_name}")

# Keep existing routers for backward compatibility
api_app.include_router(torrent_router.router, prefix="/torrent", tags=["torrent"])
api_app.include_router(
    notification_router, prefix="/notification", tags=["notification"]
)

app.mount(
    "/api/v1/static/image",
    StaticFiles(directory=config.misc.image_directory),
    name="static-images",
)

app.include_router(api_app)
app.mount("/web", StaticFiles(directory=FRONTEND_FILES_DIR, html=True), name="frontend")

# ----------------------------
# Redirects to frontend
# ----------------------------


@app.get("/")
async def root():
    return RedirectResponse(url="/web/")


@app.get("/dashboard")
async def dashboard():
    return RedirectResponse(url="/web/")


@app.get("/login")
async def login():
    return RedirectResponse(url="/web/")


# ----------------------------
# Custom Exception Handlers
# ----------------------------

app.add_exception_handler(NotFoundError, not_found_error_exception_handler)
app.add_exception_handler(MediaAlreadyExists, media_already_exists_exception_handler)
app.add_exception_handler(InvalidConfigError, invalid_config_error_exception_handler)
app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
app.add_exception_handler(UniqueViolation, sqlalchemy_integrity_error_handler)


@app.exception_handler(404)
async def not_found_handler(request, exc):
    if any(
        base_path in ["/web", "/dashboard", "/login"] for base_path in request.url.path
    ):
        return FileResponse(f"{FRONTEND_FILES_DIR}/404.html")
    return Response(content="Not Found", status_code=404)


# ----------------------------
# Hello World
# ----------------------------

log.info("Hello World!")

# ----------------------------
# Startup filesystem checks
# ----------------------------
try:
    log.info("Creating directories if they don't exist...")
    config.misc.tv_directory.mkdir(parents=True, exist_ok=True)
    config.misc.movie_directory.mkdir(parents=True, exist_ok=True)
    config.misc.torrent_directory.mkdir(parents=True, exist_ok=True)
    config.misc.image_directory.mkdir(parents=True, exist_ok=True)

    log.info("Conducting filesystem tests...")
    test_dir = config.misc.tv_directory / Path(".media_manager_test_dir")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_dir.rmdir()
    log.info(f"Successfully created test dir in TV directory at: {test_dir}")

    test_dir = config.misc.movie_directory / Path(".media_manager_test_dir")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_dir.rmdir()
    log.info(f"Successfully created test dir in Movie directory at: {test_dir}")

    test_dir = config.misc.image_directory / Path(".media_manager_test_dir")
    test_dir.touch()
    test_dir.unlink()
    log.info(f"Successfully created test file in Image directory at: {test_dir}")

    # check if hardlink creation works
    test_dir = config.misc.tv_directory / Path(".media_manager_test_dir")
    test_dir.mkdir(parents=True, exist_ok=True)

    torrent_dir = config.misc.torrent_directory / Path(".media_manager_test_dir")
    torrent_dir.mkdir(parents=True, exist_ok=True)

    test_torrent_file = torrent_dir / Path(".media_manager.test.torrent")
    test_torrent_file.touch()

    test_hardlink = test_dir / Path(".media_manager.test.hardlink")
    try:
        test_hardlink.hardlink_to(test_torrent_file)
        if not test_hardlink.samefile(test_torrent_file):
            log.critical("Hardlink creation failed!")
        log.info("Successfully created test hardlink in TV directory")
    except OSError as e:
        log.error(
            f"Hardlink creation failed, falling back to copying files. Error: {e}"
        )
        shutil.copy(src=test_torrent_file, dst=test_hardlink)
    finally:
        test_hardlink.unlink()
        test_torrent_file.unlink()
        torrent_dir.rmdir()
        test_dir.rmdir()

except Exception as e:
    log.error(f"Error creating test directory: {e}")
    raise

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5049,
        log_config=LOGGING_CONFIG,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
