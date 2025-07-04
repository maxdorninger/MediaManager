from pathlib import Path

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class BasicConfig(BaseSettings):
    image_directory: Path = Path(__file__).parent.parent / "data" / "images"
    tv_directory: Path = Path(__file__).parent.parent / "data" / "tv"
    movie_directory: Path = Path(__file__).parent.parent / "data" / "movies"
    torrent_directory: Path = Path(__file__).parent.parent / "data" / "torrents"
    FRONTEND_URL: AnyHttpUrl = "http://localhost:3000/"
    CORS_URLS: list[str] = []
    DEVELOPMENT: bool = False
