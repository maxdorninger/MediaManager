import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from starlette.responses import FileResponse, RedirectResponse
from taskiq.receiver import Receiver
from taskiq_fastapi import populate_dependency_context
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

import media_manager.movies.router as movies_router
import media_manager.torrent.router as torrent_router
import media_manager.tv.router as tv_router
from media_manager.auth.router import (
    auth_metadata_router,
    get_openid_router,
)
from media_manager.auth.router import (
    users_router as custom_users_router,
)
from media_manager.auth.schemas import UserCreate, UserRead, UserUpdate
from media_manager.auth.users import (
    bearer_auth_backend,
    cookie_auth_backend,
    fastapi_users,
)
from media_manager.config import MediaManagerConfig
from media_manager.database import init_engine
from media_manager.exceptions import (
    ConflictError,
    InvalidConfigError,
    MediaAlreadyExistsError,
    NotFoundError,
    conflict_error_handler,
    invalid_config_error_exception_handler,
    media_already_exists_exception_handler,
    not_found_error_exception_handler,
    sqlalchemy_integrity_error_handler,
)
from media_manager.filesystem_checks import run_filesystem_checks
from media_manager.logging import LOGGING_CONFIG, setup_logging
from media_manager.notification.router import router as notification_router
from media_manager.scheduler import (
    broker,
    build_scheduler_loop,
    import_all_movie_torrents_task,
    import_all_show_torrents_task,
    update_all_movies_metadata_task,
    update_all_non_ended_shows_metadata_task,
)

setup_logging()

config = MediaManagerConfig()
log = logging.getLogger(__name__)


if config.misc.development:
    log.warning("Development Mode activated!")

run_filesystem_checks(config, log)

BASE_PATH = os.getenv("BASE_PATH", "")
FRONTEND_FILES_DIR = os.getenv("FRONTEND_FILES_DIR")
DISABLE_FRONTEND_MOUNT = os.getenv("DISABLE_FRONTEND_MOUNT", "").lower() == "true"
FRONTEND_FOLLOW_SYMLINKS = os.getenv("FRONTEND_FOLLOW_SYMLINKS", "").lower() == "true"

log.info("Hello World!")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    init_engine(config.database)
    broker_started = False
    started_sources: list = []
    finish_event: asyncio.Event | None = None
    receiver_task: asyncio.Task | None = None
    loop_task: asyncio.Task | None = None
    try:
        if not broker.is_worker_process:
            await broker.startup()
            broker_started = True
        populate_dependency_context(broker, app)
        scheduler_loop = build_scheduler_loop()
        for source in scheduler_loop.scheduler.sources:
            await source.startup()
            started_sources.append(source)
        finish_event = asyncio.Event()
        receiver = Receiver(broker, run_startup=False, max_async_tasks=10)
        receiver_task = asyncio.create_task(receiver.listen(finish_event))
        loop_task = asyncio.create_task(scheduler_loop.run(skip_first_run=True))
        try:
            await asyncio.gather(
                import_all_movie_torrents_task.kiq(),
                import_all_show_torrents_task.kiq(),
                update_all_movies_metadata_task.kiq(),
                update_all_non_ended_shows_metadata_task.kiq(),
            )
        except Exception:
            log.exception("Failed to submit initial background tasks during startup.")
            raise
        yield
    finally:
        if loop_task is not None:
            loop_task.cancel()
            try:
                await loop_task
            except asyncio.CancelledError:
                pass
        if finish_event is not None and receiver_task is not None:
            finish_event.set()
            await receiver_task
        for source in started_sources:
            await source.shutdown()
        if broker_started:
            await broker.shutdown()


app = FastAPI(root_path=BASE_PATH, lifespan=lifespan)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
origins = config.misc.cors_urls
log.info(f"CORS URLs activated for following origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
app.add_middleware(CorrelationIdMiddleware, header_name="X-Correlation-ID")
api_app = APIRouter(prefix="/api/v1")


@api_app.get("/health")
async def hello_world() -> dict:
    return {"message": "Hello World!", "version": os.getenv("PUBLIC_VERSION")}


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
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
)
api_app.include_router(
    fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"]
)
api_app.include_router(custom_users_router, tags=["users"])
api_app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
api_app.include_router(auth_metadata_router, tags=["openid"])

if get_openid_router():
    api_app.include_router(get_openid_router(), tags=["openid"], prefix="/auth/oauth")

api_app.include_router(tv_router.router, prefix="/tv", tags=["tv"])
api_app.include_router(torrent_router.router, prefix="/torrent", tags=["torrent"])
api_app.include_router(movies_router.router, prefix="/movies", tags=["movie"])
api_app.include_router(
    notification_router, prefix="/notification", tags=["notification"]
)

# serve static image files
app.mount(
    "/api/v1/static/image",
    StaticFiles(directory=config.misc.image_directory),
    name="static-images",
)
app.include_router(api_app)

# handle static frontend files
if not DISABLE_FRONTEND_MOUNT:
    app.mount(
        "/web",
        StaticFiles(
            directory=FRONTEND_FILES_DIR,
            html=True,
            follow_symlink=FRONTEND_FOLLOW_SYMLINKS,
        ),
        name="frontend",
    )
    log.debug(f"Mounted frontend at /web from {FRONTEND_FILES_DIR}")
else:
    log.info("Frontend mounting disabled (DISABLE_FRONTEND_MOUNT is set)")


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse(url="/web/")


@app.get("/dashboard")
async def dashboard() -> RedirectResponse:
    return RedirectResponse(url="/web/")


@app.get("/login")
async def login() -> RedirectResponse:
    return RedirectResponse(url="/web/")


# this will serve the custom 404 page for frontend routes, so SvelteKit can handle routing
@app.exception_handler(404)
async def not_found_handler(request: Request, _exc: Exception) -> Response:
    if not DISABLE_FRONTEND_MOUNT and any(
        base_path in ["/web", "/dashboard", "/login"] for base_path in request.url.path
    ):
        return FileResponse(f"{FRONTEND_FILES_DIR}/404.html")
    return Response(content="Not Found", status_code=404)


# Register exception handlers for custom exceptions
app.add_exception_handler(NotFoundError, not_found_error_exception_handler)
app.add_exception_handler(
    MediaAlreadyExistsError, media_already_exists_exception_handler
)
app.add_exception_handler(InvalidConfigError, invalid_config_error_exception_handler)
app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
app.add_exception_handler(UniqueViolation, sqlalchemy_integrity_error_handler)
app.add_exception_handler(ConflictError, conflict_error_handler)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5049,
        log_config=LOGGING_CONFIG,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
