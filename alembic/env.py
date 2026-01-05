import sys

sys.path = ["", ".."] + sys.path[1:]


from logging.config import fileConfig  # noqa: E402

from sqlalchemy import (  # noqa: E402
    engine_from_config,
    pool,
)

from alembic import context  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

from media_manager.auth.db import OAuthAccount, User  # noqa: E402
from media_manager.config import MediaManagerConfig  # noqa: E402
from media_manager.database import Base  # noqa: E402
from media_manager.indexer.models import IndexerQueryResult  # noqa: E402
from media_manager.movies.models import Movie, MovieFile, MovieRequest  # noqa: E402
from media_manager.notification.models import Notification  # noqa: E402
from media_manager.torrent.models import Torrent  # noqa: E402
from media_manager.tv.models import (  # noqa: E402
    Episode,
    Season,
    SeasonFile,
    SeasonRequest,
    Show,
)

target_metadata = Base.metadata

# this is to keep pycharm from complaining about/optimizing unused imports
# noinspection PyStatementEffect
__all__ = [
    "User",
    "OAuthAccount",
    "IndexerQueryResult",
    "Torrent",
    "Show",
    "Season",
    "Episode",
    "SeasonFile",
    "SeasonRequest",
    "Movie",
    "MovieFile",
    "MovieRequest",
    "Notification",
]


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


db_config = MediaManagerConfig().database
db_url = f"postgresql+psycopg://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.dbname}"

config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    def include_object(object, name, type_, reflected, compare_to):
        if type_ == "table" and name == "apscheduler_jobs":
            return False
        return True

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
