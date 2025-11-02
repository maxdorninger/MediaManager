import logging
import os
from contextvars import ContextVar
from typing import Annotated, Any, Generator, Optional

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import Session, declarative_base, sessionmaker

log = logging.getLogger(__name__)

Base = declarative_base()

engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None


def build_db_url(
    user: str,
    password: str,
    host: str,
    port: int | str,
    dbname: str,
) -> str:
    db_url = URL.create(
        "postgresql+psycopg",
        user,
        password,
        host,
        port,
        dbname,
    )
    return db_url


def init_engine(
    db_config: Any | None = None,
    url: str | None = None,
) -> Engine:
    """
    Initialize the global SQLAlchemy engine and session factory.
    Pass either a DbConfig-like object or a full URL. Only initializes once.
    """
    global engine, SessionLocal
    if engine is not None:
        return engine

    if url is None:
        if db_config is None:
            url = os.getenv("DATABASE_URL")
            if not url:
                raise RuntimeError("DB config or `DATABASE_URL` must be provided")
        else:
            url = build_db_url(
                db_config.user,
                db_config.password,
                db_config.host,
                db_config.port,
                db_config.dbname,
            )

    engine = create_engine(
        url,
        echo=False,
        pool_size=10,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    log.debug("SQLAlchemy engine initialized")
    return engine


def get_engine() -> Engine:
    if engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine(...) first.")
    return engine


def get_session() -> Generator[Session, Any, None]:
    if SessionLocal is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_engine(...) first."
        )
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        log.critical(f"error occurred: {e}")
        raise
    finally:
        db.close()


db_session: ContextVar[Session] = ContextVar("db_session")
DbSessionDependency = Annotated[Session, Depends(get_session)]
