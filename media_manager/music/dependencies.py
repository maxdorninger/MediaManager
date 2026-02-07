from typing import Annotated

from fastapi import Depends, HTTPException, Path

from media_manager.database import DbSessionDependency
from media_manager.exceptions import NotFoundError
from media_manager.indexer.dependencies import indexer_service_dep
from media_manager.music.repository import MusicRepository
from media_manager.music.schemas import Album, AlbumId, Artist, ArtistId
from media_manager.music.service import MusicService
from media_manager.notification.dependencies import notification_service_dep
from media_manager.torrent.dependencies import torrent_service_dep


def get_music_repository(db_session: DbSessionDependency) -> MusicRepository:
    return MusicRepository(db_session)


music_repository_dep = Annotated[MusicRepository, Depends(get_music_repository)]


def get_music_service(
    music_repository: music_repository_dep,
    torrent_service: torrent_service_dep,
    indexer_service: indexer_service_dep,
    notification_service: notification_service_dep,
) -> MusicService:
    return MusicService(
        music_repository=music_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
        notification_service=notification_service,
    )


music_service_dep = Annotated[MusicService, Depends(get_music_service)]


def get_artist_by_id(
    music_service: music_service_dep,
    artist_id: ArtistId = Path(..., description="The ID of the artist"),
) -> Artist:
    try:
        artist = music_service.get_artist_by_id(artist_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Artist with ID {artist_id} not found.",
        ) from None
    return artist


artist_dep = Annotated[Artist, Depends(get_artist_by_id)]


def get_album_by_id(
    music_service: music_service_dep,
    album_id: AlbumId = Path(..., description="The ID of the album"),
) -> Album:
    try:
        album = music_service.music_repository.get_album(album_id=album_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Album with ID {album_id} not found.",
        ) from None
    return album


album_dep = Annotated[Album, Depends(get_album_by_id)]
