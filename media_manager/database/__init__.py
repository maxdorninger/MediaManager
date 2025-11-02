import logging
from contextvars import ContextVar
from typing import Annotated, Any, Generator

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from media_manager.config import AllEncompassingConfig

log = logging.getLogger(__name__)
config = AllEncompassingConfig().database

db_url = (
    "postgresql+psycopg"
    + "://"
    + config.user
    + ":"
    + config.password
    + "@"
    + config.host
    + ":"
    + str(config.port)
    + "/"
    + config.dbname
)

engine = create_engine(
    db_url,
    echo=False,
    pool_size=10,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
log.debug("initializing sqlalchemy declarative base")
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        log.critical(f"error occurred: {e}")
        raise e
    finally:
        db.close()


db_session: ContextVar[Session] = ContextVar("db_session")


DbSessionDependency = Annotated[Session, Depends(get_session)]
