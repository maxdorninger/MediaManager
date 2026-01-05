from typing import Annotated, Literal

from fastapi import Depends
from fastapi.exceptions import HTTPException

from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.tmdb import TmdbMetadataProvider
from media_manager.metadataProvider.tvdb import TvdbMetadataProvider


def get_metadata_provider(
    metadata_provider: Literal["tmdb", "tvdb"] = "tmdb",
) -> AbstractMetadataProvider:
    if metadata_provider == "tmdb":
        return TmdbMetadataProvider()
    elif metadata_provider == "tvdb":
        return TvdbMetadataProvider()
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metadata provider: {metadata_provider}. Supported providers are 'tmdb' and 'tvdb'.",
        )


metadata_provider_dep = Annotated[
    AbstractMetadataProvider, Depends(get_metadata_provider)
]
