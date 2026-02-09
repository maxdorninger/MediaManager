from typing import Annotated, Literal

from fastapi import Depends
from fastapi.exceptions import HTTPException

from media_manager.metadataProvider.abstract_book_metadata_provider import (
    AbstractBookMetadataProvider,
)
from media_manager.metadataProvider.openlibrary import OpenLibraryMetadataProvider


def get_book_metadata_provider(
    metadata_provider: Literal["openlibrary"] = "openlibrary",
) -> AbstractBookMetadataProvider:
    if metadata_provider == "openlibrary":
        return OpenLibraryMetadataProvider()
    raise HTTPException(
        status_code=400,
        detail=f"Invalid book metadata provider: {metadata_provider}. Supported providers are 'openlibrary'.",
    )


book_metadata_provider_dep = Annotated[
    AbstractBookMetadataProvider, Depends(get_book_metadata_provider)
]
