from pydantic import BaseModel
from media_manager.movies.schemas import MovieId
from media_manager.tv.schemas import ShowId


class MetaDataProviderSearchResult(BaseModel):
    poster_path: str | None
    overview: str | None
    name: str
    external_id: int
    year: int | None
    metadata_provider: str
    added: bool
    vote_average: float | None = None
    original_language: str | None = None
    id: MovieId | ShowId | None = None  # Internal ID if already added
