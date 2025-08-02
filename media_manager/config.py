import os
from pathlib import Path
from typing import Type, Tuple

from pydantic import AnyHttpUrl
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)

from media_manager.auth.config import AuthConfig
from media_manager.database.config import DbConfig
from media_manager.indexer.config import IndexerConfig
from media_manager.metadataProvider.config import MetadataProviderConfig
from media_manager.notification.config import NotificationConfig
from media_manager.torrent.config import TorrentConfig
from media_manager.plugins.config import MediaPluginsConfig

config_path = os.getenv("CONFIG_FILE")

if config_path is None:
    # Default to config folder approach
    config_dir = os.getenv("CONFIG_DIR", "/app/config")
    config_path = Path(config_dir) / "config.toml"
else:
    config_path = Path(config_path)


class LibraryItem(BaseSettings):
    name: str
    path: str


class BasicConfig(BaseSettings):
    image_directory: Path = Path(__file__).parent.parent / "data" / "images"
    tv_directory: Path = Path(__file__).parent.parent / "data" / "tv"
    movie_directory: Path = Path(__file__).parent.parent / "data" / "movies"
    torrent_directory: Path = Path(__file__).parent.parent / "data" / "torrents"

    frontend_url: AnyHttpUrl = "http://localhost:3000/web/"
    cors_urls: list[str] = []
    development: bool = False

    tv_libraries: list[LibraryItem] = []
    movie_libraries: list[LibraryItem] = []


class AllEncompassingConfig(BaseSettings):
    model_config = SettingsConfigDict(
        toml_file=config_path, case_sensitive=False, env_nested_delimiter="__"
    )
    """
    This class is used to load all configurations from the environment variables.
    It combines the BasicConfig with any additional configurations needed.
    """
    misc: BasicConfig = BasicConfig()
    torrents: TorrentConfig = TorrentConfig()
    notifications: NotificationConfig = NotificationConfig()
    metadata: MetadataProviderConfig = MetadataProviderConfig()
    indexers: IndexerConfig = IndexerConfig()
    database: DbConfig = DbConfig()
    auth: AuthConfig = AuthConfig()
    media_plugins: MediaPluginsConfig = MediaPluginsConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
