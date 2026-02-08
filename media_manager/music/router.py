from typing import Annotated

from fastapi import APIRouter, Depends, status

from media_manager.auth.schemas import UserRead
from media_manager.auth.users import current_active_user, current_superuser
from media_manager.config import LibraryItem, MediaManagerConfig
from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.indexer.schemas import (
    IndexerQueryResult,
    IndexerQueryResultId,
)
from media_manager.metadataProvider.music_dependencies import (
    music_metadata_provider_dep,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.music import log
from media_manager.music.dependencies import (
    album_dep,
    artist_dep,
    music_service_dep,
)
from media_manager.music.schemas import (
    Album,
    AlbumId,
    AlbumRequest,
    AlbumRequestBase,
    AlbumRequestId,
    Artist,
    ArtistId,
    CreateAlbumRequest,
    PublicAlbumFile,
    PublicArtist,
    RichAlbumRequest,
    RichArtistTorrent,
)
from media_manager.torrent.schemas import Torrent

router = APIRouter()

# -----------------------------------------------------------------------------
# METADATA & SEARCH
# -----------------------------------------------------------------------------


@router.get(
    "/search",
    dependencies=[Depends(current_active_user)],
)
def search_for_artist(
    query: str,
    music_service: music_service_dep,
    metadata_provider: music_metadata_provider_dep,
) -> list[MetaDataProviderSearchResult]:
    """
    Search for an artist on the configured music metadata provider.
    """
    return music_service.search_for_artist(
        query=query, metadata_provider=metadata_provider
    )


@router.get(
    "/recommended",
    dependencies=[Depends(current_active_user)],
)
def get_popular_artists(
    music_service: music_service_dep,
    metadata_provider: music_metadata_provider_dep,
) -> list[MetaDataProviderSearchResult]:
    """
    Get a list of trending/popular artists from ListenBrainz.
    """
    return music_service.get_popular_artists(metadata_provider=metadata_provider)


# -----------------------------------------------------------------------------
# ARTISTS
# -----------------------------------------------------------------------------


@router.get(
    "/artists",
    dependencies=[Depends(current_active_user)],
)
def get_all_artists(music_service: music_service_dep) -> list[Artist]:
    """
    Get all artists in the library.
    """
    return music_service.get_all_artists()


@router.post(
    "/artists",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_active_user)],
    responses={
        status.HTTP_201_CREATED: {
            "model": Artist,
            "description": "Successfully created artist",
        }
    },
)
def add_an_artist(
    music_service: music_service_dep,
    metadata_provider: music_metadata_provider_dep,
    artist_id: str,
) -> Artist:
    """
    Add a new artist to the library.
    """
    try:
        artist = music_service.add_artist(
            external_id=artist_id,
            metadata_provider=metadata_provider,
        )
    except ConflictError:
        artist = music_service.get_artist_by_external_id(
            external_id=artist_id, metadata_provider=metadata_provider.name
        )
        if not artist:
            raise NotFoundError from ConflictError
    return artist


@router.get(
    "/artists/torrents",
    dependencies=[Depends(current_active_user)],
)
def get_all_artists_with_torrents(
    music_service: music_service_dep,
) -> list[RichArtistTorrent]:
    """
    Get all artists that are associated with torrents.
    """
    return music_service.get_all_artists_with_torrents()


@router.get(
    "/artists/libraries",
    dependencies=[Depends(current_active_user)],
)
def get_available_libraries() -> list[LibraryItem]:
    """
    Get available music libraries from configuration.
    """
    return MediaManagerConfig().misc.music_libraries


# -----------------------------------------------------------------------------
# ALBUM REQUESTS
# -----------------------------------------------------------------------------


@router.get(
    "/albums/requests",
    dependencies=[Depends(current_active_user)],
)
def get_all_album_requests(
    music_service: music_service_dep,
) -> list[RichAlbumRequest]:
    """
    Get all album requests.
    """
    return music_service.get_all_album_requests()


@router.post(
    "/albums/requests",
    status_code=status.HTTP_201_CREATED,
)
def create_album_request(
    music_service: music_service_dep,
    album_request: CreateAlbumRequest,
    user: Annotated[UserRead, Depends(current_active_user)],
) -> AlbumRequest:
    """
    Create a new album request.
    """
    log.info(
        f"User {user.email} is creating an album request for {album_request.album_id}"
    )
    album_request: AlbumRequest = AlbumRequest.model_validate(album_request)
    album_request.requested_by = user
    if user.is_superuser:
        album_request.authorized = True
        album_request.authorized_by = user

    return music_service.add_album_request(album_request=album_request)


@router.put(
    "/albums/requests/{album_request_id}",
)
def update_album_request(
    music_service: music_service_dep,
    album_request_id: AlbumRequestId,
    update_request: AlbumRequestBase,
    user: Annotated[UserRead, Depends(current_active_user)],
) -> AlbumRequest:
    """
    Update an existing album request.
    """
    album_request = music_service.get_album_request_by_id(
        album_request_id=album_request_id
    )
    if album_request.requested_by.id != user.id or user.is_superuser:
        album_request.min_quality = update_request.min_quality
        album_request.wanted_quality = update_request.wanted_quality

    return music_service.update_album_request(album_request=album_request)


@router.patch(
    "/albums/requests/{album_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def authorize_album_request(
    music_service: music_service_dep,
    album_request_id: AlbumRequestId,
    user: Annotated[UserRead, Depends(current_superuser)],
    authorized_status: bool = False,
) -> None:
    """
    Authorize or de-authorize an album request.
    """
    album_request = music_service.get_album_request_by_id(
        album_request_id=album_request_id
    )
    album_request.authorized = authorized_status
    if authorized_status:
        album_request.authorized_by = user
    else:
        album_request.authorized_by = None
    music_service.update_album_request(album_request=album_request)


@router.delete(
    "/albums/requests/{album_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_album_request(
    music_service: music_service_dep, album_request_id: AlbumRequestId
) -> None:
    """
    Delete an album request.
    """
    music_service.delete_album_request(album_request_id=album_request_id)


# -----------------------------------------------------------------------------
# ARTISTS - SINGLE RESOURCE
# -----------------------------------------------------------------------------


@router.get(
    "/artists/{artist_id}",
    dependencies=[Depends(current_active_user)],
)
def get_artist_by_id(
    music_service: music_service_dep, artist: artist_dep
) -> PublicArtist:
    """
    Get details for a specific artist.
    """
    return music_service.get_public_artist_by_id(artist=artist)


@router.delete(
    "/artists/{artist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_an_artist(
    music_service: music_service_dep,
    artist: artist_dep,
    delete_files_on_disk: bool = False,
    delete_torrents: bool = False,
) -> None:
    """
    Delete an artist from the library.
    """
    music_service.delete_artist(
        artist=artist,
        delete_files_on_disk=delete_files_on_disk,
        delete_torrents=delete_torrents,
    )


@router.post(
    "/artists/{artist_id}/metadata",
    dependencies=[Depends(current_active_user)],
)
def update_artist_metadata(
    music_service: music_service_dep,
    artist: artist_dep,
    metadata_provider: music_metadata_provider_dep,
) -> PublicArtist:
    """
    Refresh metadata for an artist from the metadata provider.
    """
    music_service.update_artist_metadata(
        db_artist=artist, metadata_provider=metadata_provider
    )
    updated_artist = music_service.get_artist_by_id(artist_id=artist.id)
    return music_service.get_public_artist_by_id(artist=updated_artist)


@router.post(
    "/artists/{artist_id}/library",
    dependencies=[Depends(current_superuser)],
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_library(
    artist: artist_dep,
    music_service: music_service_dep,
    library: str,
) -> None:
    """
    Set the library path for an artist.
    """
    music_service.set_artist_library(artist=artist, library=library)


@router.get(
    "/artists/{artist_id}/torrents",
    dependencies=[Depends(current_active_user)],
)
def get_torrents_for_artist(
    music_service: music_service_dep,
    artist: artist_dep,
) -> RichArtistTorrent:
    """
    Get torrents associated with an artist.
    """
    return music_service.get_torrents_for_artist(artist=artist)


# -----------------------------------------------------------------------------
# ALBUMS - SINGLE RESOURCE
# -----------------------------------------------------------------------------


@router.get(
    "/albums/{album_id}",
    dependencies=[Depends(current_active_user)],
)
def get_album_by_id(album: album_dep) -> Album:
    """
    Get details for a specific album.
    """
    return Album.model_validate(album)


@router.get(
    "/albums/{album_id}/files",
    dependencies=[Depends(current_active_user)],
)
def get_album_files(
    music_service: music_service_dep,
    album: album_dep,
) -> list[PublicAlbumFile]:
    """
    Get files associated with a specific album.
    """
    return music_service.get_public_album_files(album_id=album.id)


# -----------------------------------------------------------------------------
# TORRENTS
# -----------------------------------------------------------------------------


@router.get(
    "/torrents",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
)
def search_torrents_for_album(
    music_service: music_service_dep,
    artist_id: ArtistId,
    album_name: str,
    search_query_override: str | None = None,
) -> list[IndexerQueryResult]:
    """
    Search for torrents for a specific album.
    """
    artist = music_service.get_artist_by_id(artist_id=artist_id)
    return music_service.get_all_available_torrents_for_album(
        artist=artist,
        album_name=album_name,
        search_query_override=search_query_override,
    )


@router.post(
    "/torrents",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
)
def download_a_torrent(
    music_service: music_service_dep,
    public_indexer_result_id: IndexerQueryResultId,
    artist_id: ArtistId,
    album_id: AlbumId,
    override_file_path_suffix: str = "",
) -> Torrent:
    """
    Download a torrent for a specific album.
    """
    artist = music_service.get_artist_by_id(artist_id=artist_id)
    return music_service.download_torrent(
        public_indexer_result_id=public_indexer_result_id,
        artist=artist,
        album_id=album_id,
        override_file_path_suffix=override_file_path_suffix,
    )
