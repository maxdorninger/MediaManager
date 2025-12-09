from pydantic_settings import BaseSettings


class TmdbConfig(BaseSettings):
    tmdb_relay_url: str = "https://metadata-relay.dorninger.co/tmdb"


class TvdbConfig(BaseSettings):
    tvdb_relay_url: str = "https://metadata-relay.dorninger.co/tvdb"


class MetadataProviderConfig(BaseSettings):
    tvdb: TvdbConfig = TvdbConfig()
    tmdb: TmdbConfig = TmdbConfig()
    # ISO 639-1 language codes (e.g., ["en", "no", "sv"])
    # When media's original language matches one of these, original title and metadata will be used
    primary_languages: list[str] = ["en"]
