from pydantic import BaseModel


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
