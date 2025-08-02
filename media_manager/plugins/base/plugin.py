from abc import ABC, abstractmethod
from typing import Type, List, Dict, Any, Optional
from fastapi import APIRouter

from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig
from media_manager.plugins.base.models import AbstractMediaModel


class BaseMediaPlugin(ABC):
    """
    Abstract base class for all media plugins
    """
    
    def __init__(self):
        self._service: Optional[BaseMediaService] = None
        self._repository: Optional[BaseMediaRepository] = None
    
    @property
    @abstractmethod
    def plugin_info(self) -> MediaPluginInfo:
        """Information about this plugin"""
        pass
    
    @property
    @abstractmethod
    def media_model_class(self) -> Type[Any]:
        """The SQLAlchemy model class for this media type"""
        pass
    
    @property
    @abstractmethod
    def router(self) -> APIRouter:
        """FastAPI router for this plugin's endpoints"""
        pass
    
    @abstractmethod
    def get_service(self, **dependencies) -> BaseMediaService:
        """Get the service instance for this plugin"""
        pass
    
    @abstractmethod
    def get_repository(self, session, **kwargs) -> BaseMediaRepository:
        """Get the repository instance for this plugin"""
        pass
    
    @abstractmethod
    def get_database_models(self) -> List[Type]:
        """Get all database models that need to be created for this plugin"""
        pass
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        """Validate plugin configuration"""
        return True
    
    def on_startup(self) -> None:
        """Called when the plugin is loaded"""
        pass
    
    def on_shutdown(self) -> None:
        """Called when the application shuts down"""
        pass
    
    @property
    def service(self) -> BaseMediaService:
        """Get cached service instance"""
        if self._service is None:
            raise RuntimeError("Service not initialized. Call get_service() first.")
        return self._service
    
    @property
    def repository(self) -> BaseMediaRepository:
        """Get cached repository instance"""
        if self._repository is None:
            raise RuntimeError("Repository not initialized. Call get_repository() first.")
        return self._repository