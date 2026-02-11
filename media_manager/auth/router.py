from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, status
from fastapi_users.router import get_oauth_router
from httpx_oauth.oauth2 import OAuth2
from sqlalchemy import select

from media_manager.auth.db import User
from media_manager.auth.schemas import AuthMetadata, UserRead
from media_manager.auth.users import (
    SECRET,
    create_default_admin_user,
    current_superuser,
    fastapi_users,
    openid_client,
    openid_cookie_auth_backend,
)
from media_manager.config import MediaManagerConfig
from media_manager.database import DbSessionDependency


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    await create_default_admin_user()
    yield


users_router = APIRouter(lifespan=lifespan)
auth_metadata_router = APIRouter()


def get_openid_router() -> APIRouter:
    if openid_client:
        return get_oauth_router(
            oauth_client=openid_client,
            backend=openid_cookie_auth_backend,
            get_user_manager=fastapi_users.get_user_manager,
            state_secret=SECRET,
            associate_by_email=True,
            is_verified_by_default=True,
            redirect_url=None,
        )
    # this is there, so that the appropriate routes are created even if OIDC is not configured,
    # e.g. for generating the frontend's openapi client
    return get_oauth_router(
        oauth_client=OAuth2(
            client_id="mock",
            client_secret="mock",  # noqa: S106
            authorize_endpoint="https://example.com/authorize",
            access_token_endpoint="https://example.com/token",  # noqa: S106
        ),
        backend=openid_cookie_auth_backend,
        get_user_manager=fastapi_users.get_user_manager,
        state_secret=SECRET,
        associate_by_email=False,
        is_verified_by_default=False,
        redirect_url=None,
    )


openid_config = MediaManagerConfig().auth.openid_connect


@users_router.get(
    "/users/all",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
)
def get_all_users(db: DbSessionDependency) -> list[UserRead]:
    stmt = select(User)
    result = db.execute(stmt).scalars().unique()
    return [UserRead.model_validate(user) for user in result]


@auth_metadata_router.get("/auth/metadata", status_code=status.HTTP_200_OK)
def get_auth_metadata() -> AuthMetadata:
    if openid_config.enabled:
        return AuthMetadata(oauth_providers=[openid_config.name])
    return AuthMetadata(oauth_providers=[])
