from pathlib import Path

from pydantic import BaseModel

from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult


class MediaImportSuggestion(BaseModel):
    directory: Path
    candidates: list[MetaDataProviderSearchResult]
