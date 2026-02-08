from pydantic_settings import BaseSettings


class TmdbConfig(BaseSettings):
    tmdb_relay_url: str = "https://metadata-relay.dorninger.co/tmdb"
    primary_languages: list[str] = []  # ISO 639-1 language codes
    default_language: str = "en"  # ISO 639-1 language codes


class TvdbConfig(BaseSettings):
    tvdb_relay_url: str = "https://metadata-relay.dorninger.co/tvdb"


class MusicBrainzConfig(BaseSettings):
    enabled: bool = True


class MetadataProviderConfig(BaseSettings):
    tvdb: TvdbConfig = TvdbConfig()
    tmdb: TmdbConfig = TmdbConfig()
    musicbrainz: MusicBrainzConfig = MusicBrainzConfig()
