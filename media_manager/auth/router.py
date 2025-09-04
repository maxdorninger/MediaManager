from fastapi import APIRouter, Depends
from fastapi import status
from sqlalchemy import select

from media_manager.config import AllEncompassingConfig
from media_manager.auth.db import User
from media_manager.auth.schemas import UserRead
from media_manager.auth.users import current_superuser
from media_manager.database import DbSessionDependency

users_router = APIRouter()
auth_metadata_router = APIRouter()
oauth_config = AllEncompassingConfig().auth.openid_connect


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
def get_auth_metadata() -> dict:
    if oauth_config:
        provider_names = [
            name for name, config in oauth_config.items() if config.enabled
        ]
        return {"oauth_providers": provider_names}
    else:
        return {"oauth_providers": []}
