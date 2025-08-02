from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any
from uuid import UUID

from media_manager.database import get_session
from media_manager.plugins.music.service import MusicPluginService
from media_manager.plugins.music.repository import MusicPluginRepository


def get_music_plugin_service(session: Session = Depends(get_session)) -> MusicPluginService:
    """
    Dependency to get Music plugin service
    """
    repository = MusicPluginRepository(session)
    return MusicPluginService(repository=repository)


def get_music_router() -> APIRouter:
    """
    Get the Music plugin router
    """
    router = APIRouter()
    
    @router.get("/artists")
    async def get_artists(
        limit: int = 100,
        offset: int = 0,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Get all artists"""
        return service.get_artists(limit=limit, offset=offset)
    
    @router.get("/artists/{artist_id}")
    async def get_artist(
        artist_id: UUID,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Get artist by ID"""
        artist = service.get_artist_by_id(artist_id)
        if not artist:
            raise HTTPException(status_code=404, detail="Artist not found")
        return artist
    
    @router.get("/artists/{artist_id}/albums")
    async def get_artist_albums(
        artist_id: UUID,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Get all albums by artist"""
        return service.get_albums_by_artist(artist_id)
    
    @router.get("/albums/{album_id}")
    async def get_album(
        album_id: UUID,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Get album by ID"""
        album = service.get_album_by_id(album_id)
        if not album:
            raise HTTPException(status_code=404, detail="Album not found")
        return album
    
    @router.get("/requests")
    async def get_album_requests(
        authorized_only: bool = False,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Get album requests"""
        return service.get_album_requests(authorized_only=authorized_only)
    
    @router.post("/requests")
    async def create_album_request(
        album_id: UUID,
        wanted_quality: str,
        min_quality: str,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Create an album download request"""
        return service.create_request(
            media_id=album_id,
            album_id=album_id,
            wanted_quality=wanted_quality,
            min_quality=min_quality
        )
    
    @router.post("/requests/{request_id}/authorize")
    async def authorize_album_request(
        request_id: UUID,
        user_id: UUID,
        service: MusicPluginService = Depends(get_music_plugin_service)
    ):
        """Authorize an album request"""
        return service.authorize_album_request(request_id, user_id)
    
    return router