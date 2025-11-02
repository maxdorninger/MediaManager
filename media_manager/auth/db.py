from collections.abc import AsyncGenerator
from typing import Optional

from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyBaseUserTableUUID,
    SQLAlchemyUserDatabase,
    SQLAlchemyBaseOAuthAccountTableUUID,
)
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, relationship, mapped_column

from media_manager.database import Base, build_db_url
from media_manager.config import AllEncompassingConfig


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    access_token: Mapped[str] = mapped_column(String(length=4096), nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(
        String(length=4096), nullable=True
    )
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount", lazy="joined"
    )


engine = create_async_engine(
    build_db_url(**AllEncompassingConfig().database.model_dump()), echo=False
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)
