import logging

import psycopg
from fastapi import Depends
from psycopg.rows import dict_row

from config import DbConfig, get_db_config

log = logging.getLogger(__name__)


class PgDatabase:
    """PostgreSQL Database context manager using psycopg"""

    def __init__(self) -> None:
        self.driver = psycopg

    def connect_to_database(self,  config: DbConfig = DbConfig()):
        return self.driver.connect(
            autocommit=True,
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            dbname=config.dbname,
            row_factory=dict_row
        )

    def __enter__(self):
        self.connection = self.connect_to_database()
        return self

    def __exit__(self, exception_type, exc_val, traceback):
        self.connection.close()


def init_db():
    log.info("Initializing database")

    from database import tv, users
    users.init_table()
    tv.init_table()

    log.info("Tables initialized successfully")
