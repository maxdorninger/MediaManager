from typing import Annotated, Literal

from fastapi import Depends
from fastapi.exceptions import HTTPException

from media_manager.metadataProvider.abstract_music_metadata_provider import (
    AbstractMusicMetadataProvider,
)
from media_manager.metadataProvider.musicbrainz import MusicBrainzMetadataProvider


def get_music_metadata_provider(
    metadata_provider: Literal["musicbrainz"] = "musicbrainz",
) -> AbstractMusicMetadataProvider:
    if metadata_provider == "musicbrainz":
        return MusicBrainzMetadataProvider()
    raise HTTPException(
        status_code=400,
        detail=f"Invalid music metadata provider: {metadata_provider}. Supported providers are 'musicbrainz'.",
    )


music_metadata_provider_dep = Annotated[
    AbstractMusicMetadataProvider, Depends(get_music_metadata_provider)
]
