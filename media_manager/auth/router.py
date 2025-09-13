from fastapi import APIRouter, Depends
from fastapi import status
from fastapi_users.router import get_oauth_router
from sqlalchemy import select

from media_manager.config import AllEncompassingConfig
from media_manager.auth.db import User
from media_manager.auth.schemas import UserRead, AuthMetadata
from media_manager.auth.users import (
    current_superuser,
    openid_client,
    openid_cookie_auth_backend,
    SECRET,
    fastapi_users,
)
from media_manager.database import DbSessionDependency

users_router = APIRouter()
auth_metadata_router = APIRouter()


def get_openid_router():
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
    else:
        return None


openid_config = AllEncompassingConfig().auth.openid_connect


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
    else:
        return AuthMetadata(oauth_providers=[])
