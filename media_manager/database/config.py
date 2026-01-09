from pydantic_settings import BaseSettings


class DbConfig(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    user: str = "MediaManager"
    password: str = "MediaManager"  # noqa: S105
    dbname: str = "MediaManager"
