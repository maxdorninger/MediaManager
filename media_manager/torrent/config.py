from pydantic_settings import BaseSettings, SettingsConfigDict


class QbittorrentConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QBITTORRENT_")
    host: str = "localhost"
    port: int = 8080
    username: str = "admin"
    password: str = "admin"  # noqa: S105
    enabled: bool = False

    category_name: str = "MediaManager"
    category_save_path: str = ""  # e.g."/data/torrents/mediamanager", it has to be the same directory as the torrent_directory, but from QBittorrent's container


class TransmissionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRANSMISSION_")
    path: str = "/transmission/rpc"
    https_enabled: bool = True
    host: str = "localhost"
    port: int = 9091
    username: str = ""
    password: str = ""
    enabled: bool = False


class SabnzbdConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SABNZBD_")
    host: str = "localhost"
    port: int = 8080
    api_key: str = ""
    enabled: bool = False
    base_path: str = "/api"


class TorrentConfig(BaseSettings):
    qbittorrent: QbittorrentConfig = QbittorrentConfig()
    transmission: TransmissionConfig = TransmissionConfig()
    sabnzbd: SabnzbdConfig = SabnzbdConfig()
