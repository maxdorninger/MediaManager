# MediaManager Plugin Development Guide

This guide explains how to create new media plugins for MediaManager, enabling support for additional media types like audiobooks, music, podcasts, ebooks, etc.

## Overview

MediaManager uses a plugin-based architecture where each media type (TV shows, movies, music, etc.) is handled by a separate plugin. This makes it easy to add support for new media types without modifying the core application.

## Plugin Architecture

Each plugin consists of several key components:

```
media_manager/plugins/your_media_type/
├── __init__.py          # Package initialization
├── plugin.py            # Main plugin class
├── models.py            # Database models
├── repository.py        # Data access layer
├── service.py           # Business logic
└── router.py            # API endpoints
```

## Step-by-Step Plugin Creation

### 1. Create Plugin Directory Structure

```bash
mkdir -p media_manager/plugins/your_media_type
touch media_manager/plugins/your_media_type/__init__.py
```

### 2. Define Database Models (`models.py`)

Create SQLAlchemy models that follow the common media patterns:

```python
from uuid import UUID
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.database import Base
from media_manager.torrent.models import Quality

class YourMainMedia(Base):
    __tablename__ = "your_main_media"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)
    
    # Common media fields (required for all media types)
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str]
    year: Mapped[int | None]
    library: Mapped[str] = mapped_column(default="")
    
    # Your media-specific fields
    # Add any fields specific to your media type
    
    # Relationships
    files: Mapped[list["YourMediaFile"]] = relationship(
        back_populates="media", cascade="all, delete"
    )
    requests: Mapped[list["YourMediaRequest"]] = relationship(
        back_populates="media", cascade="all, delete"
    )

class YourMediaFile(Base):
    __tablename__ = "your_media_file"
    __table_args__ = (PrimaryKeyConstraint("media_id", "file_path_suffix"),)
    
    # Common file fields
    media_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="your_main_media.id", ondelete="CASCADE"),
    )
    file_path_suffix: Mapped[str]
    quality: Mapped[Quality]
    torrent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="torrent.id", ondelete="SET NULL"),
    )
    
    torrent = relationship("Torrent", uselist=False)
    media = relationship("YourMainMedia", back_populates="files", uselist=False)

class YourMediaRequest(Base):
    __tablename__ = "your_media_request"
    __table_args__ = (UniqueConstraint("media_id", "wanted_quality"),)
    
    # Common request fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    wanted_quality: Mapped[Quality]
    min_quality: Mapped[Quality]
    authorized: Mapped[bool] = mapped_column(default=False)
    
    requested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )
    authorized_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="user.id", ondelete="SET NULL"),
    )
    
    # Media-specific fields
    media_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="your_main_media.id", ondelete="CASCADE"),
    )
    
    requested_by = relationship("User", foreign_keys=[requested_by_id], uselist=False)
    authorized_by = relationship("User", foreign_keys=[authorized_by_id], uselist=False)
    media = relationship("YourMainMedia", back_populates="requests", uselist=False)
```

### 3. Create Repository (`repository.py`)

The repository handles database operations:

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.your_media_type.models import YourMainMedia, YourMediaRequest

class YourMediaRepository(BaseMediaRepository[YourMainMedia]):
    def __init__(self, session: Session):
        super().__init__(session, YourMainMedia)
    
    def get_downloadable_requests(self) -> List[YourMediaRequest]:
        """Get requests that are ready for download"""
        stmt = select(YourMediaRequest).where(YourMediaRequest.authorized == True)
        return list(self.session.execute(stmt).scalars())
    
    def get_files_by_media_id(self, media_id: UUID) -> List:
        """Get files for specific media"""
        # Implement based on your media structure
        pass
    
    # Add your media-specific repository methods
    def get_media_by_id(self, media_id: UUID) -> Optional[YourMainMedia]:
        return self.session.get(YourMainMedia, media_id)
    
    def create_media(self, **kwargs) -> YourMainMedia:
        media = YourMainMedia(**kwargs)
        self.session.add(media)
        self.session.commit()
        self.session.refresh(media)
        return media
    
    def create_request(self, **kwargs) -> YourMediaRequest:
        request = YourMediaRequest(**kwargs)
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request
```

### 4. Implement Service Layer (`service.py`)

The service contains business logic:

```python
from typing import List, Optional, Any
from uuid import UUID

from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.schemas import MediaPluginInfo
from media_manager.plugins.your_media_type.repository import YourMediaRepository
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.indexer.schemas import IndexerQueryResult

class YourMediaService(BaseMediaService):
    def __init__(self, repository: YourMediaRepository, **dependencies):
        super().__init__(repository)
        self.repository = repository
        # Initialize any dependencies (metadata providers, etc.)
    
    def search_metadata(self, query: str, **kwargs) -> List[MetaDataProviderSearchResult]:
        """Search for media in metadata providers"""
        # Implement metadata search for your media type
        # This might connect to APIs like MusicBrainz, Goodreads, etc.
        return []
    
    def create_from_metadata(self, metadata_result: MetaDataProviderSearchResult, **kwargs) -> Any:
        """Create media from metadata provider result"""
        # Create your media type from metadata
        return self.repository.create_media(
            external_id=metadata_result.external_id,
            name=metadata_result.name,
            overview=metadata_result.overview,
            year=metadata_result.year,
            metadata_provider=metadata_result.metadata_provider,
            **kwargs
        )
    
    def update_metadata(self, media_id: UUID) -> Optional[Any]:
        """Update metadata for existing media"""
        # Implement metadata updates
        pass
    
    def search_torrents(self, media_id: UUID, **kwargs) -> List[IndexerQueryResult]:
        """Search for torrents for this media"""
        # Implement torrent searching logic
        return []
    
    def create_request(self, media_id: UUID, **kwargs) -> Any:
        """Create a download request"""
        return self.repository.create_request(media_id=media_id, **kwargs)
    
    def auto_download_approved_requests(self) -> None:
        """Automatically download approved requests"""
        requests = self.repository.get_downloadable_requests()
        for request in requests:
            # Implement auto-download logic
            pass
    
    def import_downloaded_files(self) -> None:
        """Import downloaded files from torrent directory"""
        # Implement file import logic specific to your media type
        pass
    
    def get_plugin_info(self) -> MediaPluginInfo:
        """Get information about this plugin"""
        return MediaPluginInfo(
            name="your_media_type",
            display_name="Your Media Type",
            version="1.0.0",
            description="Manage your media type with automatic downloading",
            media_type="your_media_type",
            supported_extensions=[".ext1", ".ext2"],  # Your file extensions
            metadata_providers=["your_provider"]  # Your metadata providers
        )
```

### 5. Create API Routes (`router.py`)

Define FastAPI endpoints:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from media_manager.database import get_session
from media_manager.plugins.your_media_type.service import YourMediaService
from media_manager.plugins.your_media_type.repository import YourMediaRepository

def get_service(session: Session = Depends(get_session)) -> YourMediaService:
    repository = YourMediaRepository(session)
    return YourMediaService(repository=repository)

def get_router() -> APIRouter:
    router = APIRouter()
    
    @router.get("/")
    async def get_all_media(
        limit: int = 100,
        offset: int = 0,
        service: YourMediaService = Depends(get_service)
    ):
        """Get all media items"""
        return service.get_all(limit=limit, offset=offset)
    
    @router.get("/{media_id}")
    async def get_media(
        media_id: UUID,
        service: YourMediaService = Depends(get_service)
    ):
        """Get media by ID"""
        media = service.get_by_id(media_id)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")
        return media
    
    @router.post("/requests")
    async def create_request(
        media_id: UUID,
        wanted_quality: str,
        min_quality: str,
        service: YourMediaService = Depends(get_service)
    ):
        """Create a download request"""
        return service.create_request(
            media_id=media_id,
            wanted_quality=wanted_quality,
            min_quality=min_quality
        )
    
    return router
```

### 6. Main Plugin Class (`plugin.py`)

Tie everything together:

```python
from typing import Type, List
from fastapi import APIRouter

from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig
from media_manager.plugins.your_media_type.models import YourMainMedia, YourMediaFile, YourMediaRequest
from media_manager.plugins.your_media_type.service import YourMediaService
from media_manager.plugins.your_media_type.repository import YourMediaRepository
from media_manager.plugins.your_media_type.router import get_router

class YourMediaPlugin(BaseMediaPlugin):
    @property
    def plugin_info(self) -> MediaPluginInfo:
        return MediaPluginInfo(
            name="your_media_type",
            display_name="Your Media Type",
            version="1.0.0",
            description="Manage your media type with automatic downloading",
            media_type="your_media_type",
            supported_extensions=[".ext1", ".ext2"],
            metadata_providers=["your_provider"]
        )
    
    @property
    def media_model_class(self) -> Type[YourMainMedia]:
        return YourMainMedia
    
    @property
    def router(self) -> APIRouter:
        return get_router()
    
    def get_service(self, **dependencies) -> BaseMediaService:
        session = dependencies.get('session')
        if not session:
            raise ValueError("Session dependency is required")
        
        repository = self.get_repository(session)
        self._service = YourMediaService(repository, **dependencies)
        return self._service
    
    def get_repository(self, session, **kwargs) -> BaseMediaRepository:
        self._repository = YourMediaRepository(session)
        return self._repository
    
    def get_database_models(self) -> List[Type]:
        return [YourMainMedia, YourMediaFile, YourMediaRequest]
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        """Validate plugin configuration"""
        if not config.libraries:
            return False
        
        for library in config.libraries:
            # Handle both dict and object forms
            if isinstance(library, dict):
                enabled = library.get('enabled', True)
                path = library.get('path', '')
            else:
                enabled = getattr(library, 'enabled', True)
                path = getattr(library, 'path', '')
            
            if enabled and not path:
                return False
        
        return True
    
    def on_startup(self) -> None:
        print(f"Your Media Plugin v{self.plugin_info.version} started")
    
    def on_shutdown(self) -> None:
        print("Your Media Plugin shutting down")
```

### 7. Add Configuration

Update `config.example.toml`:

```toml
# Your Media Type Plugin
[media_plugins.your_media_type]
enabled = false  # Set to true to enable
auto_download = true
update_metadata_interval = "weekly"
import_check_interval = "15min"
preferred_quality = "high"
minimum_quality = "medium"
create_subdirectories = true
file_naming_pattern = "{name} ({year})"

[[media_plugins.your_media_type.libraries]]
name = "Your Media"
path = "/data/media/your_media_type"
enabled = true
```

### 8. Write Tests

Create comprehensive tests in `tests/plugins/test_your_media_plugin.py`:

```python
import pytest
from unittest.mock import Mock
from uuid import uuid4

from media_manager.plugins.your_media_type.plugin import YourMediaPlugin
from media_manager.plugins.base.schemas import MediaPluginConfig

@pytest.fixture
def plugin():
    return YourMediaPlugin()

def test_plugin_info(plugin):
    info = plugin.plugin_info
    assert info.name == "your_media_type"
    assert info.display_name == "Your Media Type"
    assert info.media_type == "your_media_type"

def test_validate_config_valid(plugin):
    config = MediaPluginConfig(
        enabled=True,
        libraries=[{"name": "Test", "path": "/data/test", "enabled": True}]
    )
    assert plugin.validate_config(config) is True

# Add more tests for all components
```

## Plugin Discovery and Loading

Plugins are automatically discovered and loaded by the plugin manager:

1. **Discovery**: The plugin manager scans `media_manager/plugins/` for directories containing a `plugin.py` file
2. **Loading**: Each plugin's main class (inheriting from `BaseMediaPlugin`) is instantiated
3. **Registration**: Plugin routers are automatically registered with FastAPI
4. **Database**: Plugin database models are included in schema creation

## Best Practices

### 1. Follow Naming Conventions
- Plugin directory: `media_manager/plugins/media_type_name/`
- Main model: Singular noun (e.g., `Book`, `Album`, `Podcast`)
- File model: `{Media}File` (e.g., `BookFile`, `AlbumFile`)
- Request model: `{Media}Request` (e.g., `BookRequest`, `AlbumRequest`)

### 2. Common Fields
All media types should have these common fields:
- `id`: UUID primary key
- `external_id`: ID from metadata provider
- `metadata_provider`: Source of metadata (e.g., "tmdb", "musicbrainz")
- `name`: Display name
- `overview`: Description
- `year`: Release year
- `library`: Library path/name

### 3. Database Constraints
- Add `UniqueConstraint("external_id", "metadata_provider")` to prevent duplicates
- Use proper foreign key constraints with cascade rules
- Add indexes for frequently queried fields

### 4. Error Handling
- Use proper exception handling in services
- Return appropriate HTTP status codes in routers
- Log errors appropriately

### 5. Configuration
- Support multiple library paths
- Allow enabling/disabling per plugin
- Provide sensible defaults

## Integration Points

### Metadata Providers
Integrate with external APIs to fetch metadata:
- Music: MusicBrainz, Last.FM, Discogs
- Books: Goodreads, Open Library
- Podcasts: iTunes, Spotify

### Indexers
Use existing indexer system to search for downloads:
- Configure search parameters specific to your media type
- Handle quality preferences
- Implement scoring rules

### File Organization
- Respect library paths from configuration
- Use configurable naming patterns
- Handle file extensions appropriately

## Example: Complete Ebook Plugin

See the step-by-step example in the next section for a complete implementation of an ebook plugin.

## Testing Your Plugin

1. **Unit Tests**: Test individual components (repository, service, plugin)
2. **Integration Tests**: Test with database and API endpoints
3. **Configuration Tests**: Verify configuration validation works
4. **End-to-End Tests**: Test the complete workflow

## Debugging

### Common Issues
1. **Import Errors**: Check for circular imports, especially with database models
2. **Configuration Issues**: Verify TOML syntax and plugin configuration
3. **Database Errors**: Ensure proper migrations are created
4. **Router Issues**: Check FastAPI route definitions and dependencies

### Logging
Add logging to your plugin for debugging:

```python
import logging
log = logging.getLogger(__name__)

def your_method(self):
    log.info(f"Processing {self.plugin_info.display_name}")
    log.debug(f"Method parameters: {locals()}")
```

## Performance Considerations

1. **Database Queries**: Use efficient queries with proper joins
2. **Caching**: Consider caching metadata and search results
3. **Background Tasks**: Use async operations for long-running tasks
4. **Rate Limiting**: Respect API rate limits for metadata providers

## Security

1. **Input Validation**: Validate all user inputs
2. **SQL Injection**: Use parameterized queries (SQLAlchemy handles this)
3. **File Paths**: Validate file paths to prevent directory traversal
4. **API Keys**: Store API keys securely in configuration

## Database Migrations

**Important**: Each new plugin will need its own database migration when first implemented. This is expected and required for proper database schema management.

When you create a new plugin with database models:

1. **Create the migration**:
   ```bash
   uv run alembic revision --autogenerate -m "Add [plugin_name] plugin models"
   ```

2. **Apply the migration**:
   ```bash
   uv run alembic upgrade head
   ```

3. **Test the migration** works correctly on a fresh database

This ensures your plugin's database tables are properly created and tracked in the migration history. The plugin system automatically includes your models in the database schema, but migrations must be explicitly created for each new plugin.

This guide provides a comprehensive foundation for creating new media plugins in MediaManager. The plugin system is designed to be flexible and extensible while maintaining consistency across different media types.