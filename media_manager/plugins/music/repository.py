from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.music.models import Artist, Album, Track, AlbumFile, AlbumRequest


class MusicPluginRepository(BaseMediaRepository[Artist]):
    """
    Music Plugin repository for managing artists, albums, and tracks
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Artist)
    
    def get_downloadable_requests(self) -> List[AlbumRequest]:
        """Get album requests that are ready for download"""
        stmt = select(AlbumRequest).where(
            AlbumRequest.authorized == True
        )
        return list(self.session.execute(stmt).scalars())
    
    def get_files_by_media_id(self, media_id: UUID) -> List[AlbumFile]:
        """Get album files for a specific artist (all albums)"""
        stmt = select(AlbumFile).join(Album).where(Album.artist_id == media_id)
        return list(self.session.execute(stmt).scalars())
    
    # Artist-specific methods
    def get_artist_by_id(self, artist_id: UUID) -> Optional[Artist]:
        return self.session.get(Artist, artist_id)
    
    def get_artists(self, limit: int = 100, offset: int = 0) -> List[Artist]:
        stmt = select(Artist).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars())
    
    def create_artist(self, **kwargs) -> Artist:
        artist = Artist(**kwargs)
        self.session.add(artist)
        self.session.commit()
        self.session.refresh(artist)
        return artist
    
    # Album-specific methods
    def get_album_by_id(self, album_id: UUID) -> Optional[Album]:
        return self.session.get(Album, album_id)
    
    def get_albums_by_artist(self, artist_id: UUID) -> List[Album]:
        stmt = select(Album).where(Album.artist_id == artist_id)
        return list(self.session.execute(stmt).scalars())
    
    def create_album(self, **kwargs) -> Album:
        album = Album(**kwargs)
        self.session.add(album)
        self.session.commit()
        self.session.refresh(album)
        return album
    
    # Album request methods
    def create_album_request(self, **kwargs) -> AlbumRequest:
        request = AlbumRequest(**kwargs)
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request
    
    def get_album_requests(self, authorized_only: bool = False) -> List[AlbumRequest]:
        stmt = select(AlbumRequest)
        if authorized_only:
            stmt = stmt.where(AlbumRequest.authorized == True)
        return list(self.session.execute(stmt).scalars())
    
    def update_album_request(self, request_id: UUID, **kwargs) -> Optional[AlbumRequest]:
        request = self.session.get(AlbumRequest, request_id)
        if request:
            for key, value in kwargs.items():
                setattr(request, key, value)
            self.session.commit()
            self.session.refresh(request)
        return request