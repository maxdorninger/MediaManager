from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

# Removed imports that caused circular dependencies

T = TypeVar('T')


class BaseMediaRepository(ABC, Generic[T]):
    """
    Abstract base repository for media types
    """
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    def get_by_id(self, media_id: UUID) -> Optional[T]:
        """Get media by ID"""
        return self.session.get(self.model_class, media_id)
    
    def get_by_external_id(self, external_id: int, metadata_provider: str) -> Optional[T]:
        """Get media by external ID and metadata provider"""
        stmt = select(self.model_class).where(
            self.model_class.external_id == external_id,
            self.model_class.metadata_provider == metadata_provider
        )
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all media with pagination"""
        stmt = select(self.model_class).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars())
    
    def search_by_name(self, name: str, limit: int = 20) -> List[T]:
        """Search media by name"""
        stmt = select(self.model_class).where(
            self.model_class.name.ilike(f"%{name}%")
        ).limit(limit)
        return list(self.session.execute(stmt).scalars())
    
    def create(self, **kwargs) -> T:
        """Create new media"""
        media = self.model_class(**kwargs)
        self.session.add(media)
        self.session.commit()
        self.session.refresh(media)
        return media
    
    def update(self, media_id: UUID, **kwargs) -> Optional[T]:
        """Update existing media"""
        media = self.get_by_id(media_id)
        if media:
            for key, value in kwargs.items():
                setattr(media, key, value)
            self.session.commit()
            self.session.refresh(media)
        return media
    
    def delete(self, media_id: UUID) -> bool:
        """Delete media"""
        media = self.get_by_id(media_id)
        if media:
            self.session.delete(media)
            self.session.commit()
            return True
        return False
    
    @abstractmethod
    def get_downloadable_requests(self) -> List[Any]:
        """Get requests that are ready for download - plugin specific"""
        pass
    
    @abstractmethod
    def get_files_by_media_id(self, media_id: UUID) -> List[Any]:
        """Get files for specific media - plugin specific"""
        pass