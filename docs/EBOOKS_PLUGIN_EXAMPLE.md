# Complete Example: Creating an Ebooks Plugin

This document provides a complete, step-by-step example of creating an ebooks plugin for MediaManager. This demonstrates how to add support for a new media type from scratch.

## Overview

We'll create an ebooks plugin that supports:
- **Authors** and **Books** (one-to-many relationship)
- **Series** support (books can belong to a series)
- **Multiple file formats** (.epub, .pdf, .mobi, etc.)
- **Metadata from Open Library API**
- **Quality preferences** (Original, High, Medium, Low based on file format)

## Step 1: Create Plugin Structure

```bash
mkdir -p media_manager/plugins/ebooks
touch media_manager/plugins/ebooks/__init__.py
```

## Step 2: Database Models (`models.py`)

```python
from uuid import UUID
from sqlalchemy import ForeignKey, PrimaryKeyConstraint, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from media_manager.database import Base
from media_manager.torrent.models import Quality


class Author(Base):
    __tablename__ = "author"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)
    
    # Common media fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str] = mapped_column(default="")  # Biography
    year: Mapped[int | None]  # Birth year
    library: Mapped[str] = mapped_column(default="")
    
    # Author-specific fields
    birth_date: Mapped[str] = mapped_column(default="")
    death_date: Mapped[str] = mapped_column(default="")
    nationality: Mapped[str] = mapped_column(default="")
    genres: Mapped[str] = mapped_column(default="")  # Comma-separated
    
    # Relationships
    books: Mapped[list["Book"]] = relationship(
        back_populates="author", cascade="all, delete"
    )


class Series(Base):
    __tablename__ = "series"
    __table_args__ = (UniqueConstraint("external_id", "metadata_provider"),)
    
    # Common media fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]
    overview: Mapped[str] = mapped_column(default="")
    year: Mapped[int | None]  # Start year
    library: Mapped[str] = mapped_column(default="")
    
    # Series-specific fields
    total_books: Mapped[int] = mapped_column(default=0)
    completed: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    books: Mapped[list["Book"]] = relationship(
        back_populates="series", cascade="all, delete"
    )


class Book(Base):
    __tablename__ = "book"
    __table_args__ = (
        UniqueConstraint("external_id", "metadata_provider"),
        UniqueConstraint("author_id", "title", "series_id", "series_number"),
    )
    
    # Common media fields
    id: Mapped[UUID] = mapped_column(primary_key=True)
    external_id: Mapped[int]
    metadata_provider: Mapped[str]
    name: Mapped[str]  # Title
    overview: Mapped[str] = mapped_column(default="")  # Description
    year: Mapped[int | None]  # Publication year
    library: Mapped[str] = mapped_column(default="")
    
    # Book-specific fields
    title: Mapped[str]  # Alias for name
    isbn: Mapped[str] = mapped_column(default="")
    isbn13: Mapped[str] = mapped_column(default="")
    language: Mapped[str] = mapped_column(default="en")
    pages: Mapped[int] = mapped_column(default=0)
    publisher: Mapped[str] = mapped_column(default="")
    publication_date: Mapped[str] = mapped_column(default="")
    genres: Mapped[str] = mapped_column(default="")  # Comma-separated
    
    # Relationships
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="author.id", ondelete="CASCADE"),
    )
    series_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="series.id", ondelete="SET NULL"),
    )
    series_number: Mapped[int | None] = mapped_column(default=None)
    
    author: Mapped["Author"] = relationship(back_populates="books")
    series: Mapped["Series"] = relationship(back_populates="books")
    
    book_files = relationship(
        "BookFile", back_populates="book", cascade="all, delete"
    )
    book_requests = relationship(
        "BookRequest", back_populates="book", cascade="all, delete"
    )
    
    @property
    def display_name(self) -> str:
        """Get display name for the book"""
        if self.series and self.series_number:
            return f"{self.title} (#{self.series_number} in {self.series.name})"
        return self.title


class BookFile(Base):
    __tablename__ = "book_file"
    __table_args__ = (PrimaryKeyConstraint("book_id", "file_path_suffix"),)
    
    # Common file fields
    book_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="book.id", ondelete="CASCADE"),
    )
    file_path_suffix: Mapped[str]
    quality: Mapped[Quality]
    torrent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(column="torrent.id", ondelete="SET NULL"),
    )
    
    # Book-specific file fields
    format: Mapped[str] = mapped_column(default="")  # epub, pdf, mobi, etc.
    file_size: Mapped[int] = mapped_column(default=0)  # in bytes
    
    torrent = relationship("Torrent", uselist=False)
    book = relationship("Book", back_populates="book_files", uselist=False)


class BookRequest(Base):
    __tablename__ = "book_request"
    __table_args__ = (UniqueConstraint("book_id", "wanted_quality"),)
    
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
    
    # Book-specific fields
    book_id: Mapped[UUID] = mapped_column(
        ForeignKey(column="book.id", ondelete="CASCADE"),
    )
    preferred_formats: Mapped[str] = mapped_column(default="epub,pdf,mobi")  # Comma-separated
    
    requested_by = relationship("User", foreign_keys=[requested_by_id], uselist=False)
    authorized_by = relationship("User", foreign_keys=[authorized_by_id], uselist=False)
    book = relationship("Book", back_populates="book_requests", uselist=False)
```

## Step 3: Repository Layer (`repository.py`)

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.ebooks.models import Author, Book, Series, BookFile, BookRequest


class EbookRepository(BaseMediaRepository[Author]):
    """
    Ebook repository for managing authors, books, and series
    """
    
    def __init__(self, session: Session):
        super().__init__(session, Author)
    
    def get_downloadable_requests(self) -> List[BookRequest]:
        """Get book requests that are ready for download"""
        stmt = select(BookRequest).where(BookRequest.authorized == True)
        return list(self.session.execute(stmt).scalars())
    
    def get_files_by_media_id(self, media_id: UUID) -> List[BookFile]:
        """Get book files for a specific author (all books)"""
        stmt = (
            select(BookFile)
            .join(Book)
            .where(Book.author_id == media_id)
        )
        return list(self.session.execute(stmt).scalars())
    
    # Author-specific methods
    def get_author_by_id(self, author_id: UUID) -> Optional[Author]:
        return self.session.get(Author, author_id)
    
    def get_authors(self, limit: int = 100, offset: int = 0) -> List[Author]:
        stmt = select(Author).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars())
    
    def create_author(self, **kwargs) -> Author:
        author = Author(**kwargs)
        self.session.add(author)
        self.session.commit()
        self.session.refresh(author)
        return author
    
    # Book-specific methods
    def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        return self.session.get(Book, book_id)
    
    def get_books(self, limit: int = 100, offset: int = 0) -> List[Book]:
        stmt = select(Book).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars())
    
    def get_books_by_author(self, author_id: UUID) -> List[Book]:
        stmt = select(Book).where(Book.author_id == author_id)
        return list(self.session.execute(stmt).scalars())
    
    def get_books_by_series(self, series_id: UUID) -> List[Book]:
        stmt = (
            select(Book)
            .where(Book.series_id == series_id)
            .order_by(Book.series_number)
        )
        return list(self.session.execute(stmt).scalars())
    
    def create_book(self, **kwargs) -> Book:
        book = Book(**kwargs)
        self.session.add(book)
        self.session.commit()
        self.session.refresh(book)
        return book
    
    # Series-specific methods
    def get_series_by_id(self, series_id: UUID) -> Optional[Series]:
        return self.session.get(Series, series_id)
    
    def get_series(self, limit: int = 100, offset: int = 0) -> List[Series]:
        stmt = select(Series).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars())
    
    def create_series(self, **kwargs) -> Series:
        series = Series(**kwargs)
        self.session.add(series)
        self.session.commit()
        self.session.refresh(series)
        return series
    
    # Request methods
    def create_book_request(self, **kwargs) -> BookRequest:
        request = BookRequest(**kwargs)
        self.session.add(request)
        self.session.commit()
        self.session.refresh(request)
        return request
    
    def get_book_requests(self, authorized_only: bool = False) -> List[BookRequest]:
        stmt = select(BookRequest)
        if authorized_only:
            stmt = stmt.where(BookRequest.authorized == True)
        return list(self.session.execute(stmt).scalars())
    
    def update_book_request(self, request_id: UUID, **kwargs) -> Optional[BookRequest]:
        request = self.session.get(BookRequest, request_id)
        if request:
            for key, value in kwargs.items():
                setattr(request, key, value)
            self.session.commit()
            self.session.refresh(request)
        return request
    
    # Search methods
    def search_books_by_title(self, title: str, limit: int = 20) -> List[Book]:
        stmt = (
            select(Book)
            .where(Book.title.ilike(f"%{title}%"))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())
    
    def search_authors_by_name(self, name: str, limit: int = 20) -> List[Author]:
        stmt = (
            select(Author)
            .where(Author.name.ilike(f"%{name}%"))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())
```

## Step 4: Service Layer (`service.py`)

```python
from typing import List, Optional, Any, Dict
from uuid import UUID
import logging

from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.schemas import MediaPluginInfo
from media_manager.plugins.ebooks.repository import EbookRepository
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.indexer.schemas import IndexerQueryResult

log = logging.getLogger(__name__)


class EbookService(BaseMediaService):
    """
    Ebook service for managing authors, books, and series
    """
    
    def __init__(self, repository: EbookRepository, **dependencies):
        super().__init__(repository)
        self.repository = repository
        # In a real implementation, you'd initialize metadata providers here
        # e.g., self.open_library_client = dependencies.get('open_library_client')
    
    def search_metadata(self, query: str, **kwargs) -> List[MetaDataProviderSearchResult]:
        """Search for books/authors in metadata providers"""
        # Placeholder for Open Library API integration
        # Real implementation would:
        # 1. Search Open Library API
        # 2. Parse results into MetaDataProviderSearchResult objects
        # 3. Handle pagination
        
        log.info(f"Searching for books: {query}")
        return []  # Placeholder
    
    def create_from_metadata(self, metadata_result: MetaDataProviderSearchResult, **kwargs) -> Any:
        """Create book/author from metadata provider result"""
        # This would create books and authors from Open Library data
        # Including handling of series, ISBNs, etc.
        
        author_name = kwargs.get('author_name', 'Unknown Author')
        
        # Create or get author
        author = self._get_or_create_author(author_name, metadata_result.metadata_provider)
        
        # Create book
        book = self.repository.create_book(
            external_id=metadata_result.external_id,
            title=metadata_result.name,
            name=metadata_result.name,  # Alias for title
            overview=metadata_result.overview,
            year=metadata_result.year,
            metadata_provider=metadata_result.metadata_provider,
            author_id=author.id,
            **kwargs
        )
        
        return book
    
    def _get_or_create_author(self, name: str, metadata_provider: str) -> Any:
        """Get existing author or create new one"""
        # Search for existing author
        authors = self.repository.search_authors_by_name(name, limit=1)
        if authors:
            return authors[0]
        
        # Create new author
        return self.repository.create_author(
            external_id=0,  # Would get from metadata provider
            name=name,
            overview="",
            metadata_provider=metadata_provider
        )
    
    def update_metadata(self, media_id: UUID) -> Optional[Any]:
        """Update metadata for existing author/book"""
        # Implementation would refresh data from metadata providers
        author = self.repository.get_author_by_id(media_id)
        if author:
            log.info(f"Updating metadata for author: {author.name}")
            # Update author and all their books
        return author
    
    def search_torrents(self, media_id: UUID, **kwargs) -> List[IndexerQueryResult]:
        """Search for torrents for book"""
        book_id = kwargs.get('book_id')
        if book_id:
            book = self.repository.get_book_by_id(book_id)
            if book:
                # Search for "{author} {title}" or "{title} {author}"
                queries = [
                    f"{book.author.name} {book.title}",
                    f"{book.title} {book.author.name}",
                ]
                
                # Add series info if available
                if book.series:
                    queries.append(f"{book.series.name} {book.series_number}")
                
                log.info(f"Searching torrents for book: {book.title}")
                # Would use indexer service to search
                return []
        
        return []
    
    def create_request(self, media_id: UUID, **kwargs) -> Any:
        """Create a book download request"""
        book_id = kwargs.get('book_id', media_id)
        return self.repository.create_book_request(
            book_id=book_id,
            **kwargs
        )
    
    def auto_download_approved_requests(self) -> None:
        """Automatically download approved book requests"""
        requests = self.repository.get_downloadable_requests()
        log.info(f"Processing {len(requests)} approved book requests")
        
        for request in requests:
            try:
                # Search for torrents
                torrents = self.search_torrents(
                    media_id=request.book_id,
                    book_id=request.book_id
                )
                
                # Filter by quality and format preferences
                # Implement download logic
                log.info(f"Auto-downloading book: {request.book.title}")
                
            except Exception as e:
                log.error(f"Error auto-downloading book {request.book.title}: {e}")
    
    def import_downloaded_files(self) -> None:
        """Import downloaded ebook files from torrent directory"""
        # Implementation would:
        # 1. Scan torrent directory for ebook files
        # 2. Extract metadata from files (title, author, etc.)
        # 3. Match to existing books or create new ones
        # 4. Move/organize files according to naming pattern
        # 5. Update database with file information
        
        log.info("Scanning for downloaded ebook files")
        # Placeholder implementation
    
    def get_plugin_info(self) -> MediaPluginInfo:
        """Get information about this plugin"""
        return MediaPluginInfo(
            name="ebooks",
            display_name="Ebooks",
            version="1.0.0",
            description="Manage ebooks with automatic downloading and organization",
            media_type="ebook",
            supported_extensions=[".epub", ".pdf", ".mobi", ".azw", ".azw3", ".fb2", ".txt"],
            metadata_providers=["openlibrary", "goodreads"]
        )
    
    # Ebook-specific methods
    def get_author_by_id(self, author_id: UUID):
        return self.repository.get_author_by_id(author_id)
    
    def get_authors(self, limit: int = 100, offset: int = 0):
        return self.repository.get_authors(limit, offset)
    
    def get_book_by_id(self, book_id: UUID):
        return self.repository.get_book_by_id(book_id)
    
    def get_books(self, limit: int = 100, offset: int = 0):
        return self.repository.get_books(limit, offset)
    
    def get_books_by_author(self, author_id: UUID):
        return self.repository.get_books_by_author(author_id)
    
    def get_series_by_id(self, series_id: UUID):
        return self.repository.get_series_by_id(series_id)
    
    def get_books_by_series(self, series_id: UUID):
        return self.repository.get_books_by_series(series_id)
    
    def get_book_requests(self, **kwargs):
        return self.repository.get_book_requests(**kwargs)
    
    def authorize_book_request(self, request_id: UUID, user_id: UUID):
        return self.repository.update_book_request(
            request_id, 
            authorized=True, 
            authorized_by_id=user_id
        )
    
    def search_books(self, query: str, limit: int = 20):
        """Search books by title"""
        return self.repository.search_books_by_title(query, limit)
    
    def search_authors(self, query: str, limit: int = 20):
        """Search authors by name"""
        return self.repository.search_authors_by_name(query, limit)
```

## Step 5: API Routes (`router.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from media_manager.database import get_session
from media_manager.plugins.ebooks.service import EbookService
from media_manager.plugins.ebooks.repository import EbookRepository


def get_ebook_service(session: Session = Depends(get_session)) -> EbookService:
    """Dependency to get Ebook service"""
    repository = EbookRepository(session)
    return EbookService(repository=repository)


def get_ebook_router() -> APIRouter:
    """Get the Ebook plugin router"""
    router = APIRouter()
    
    # Author endpoints
    @router.get("/authors")
    async def get_authors(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        search: Optional[str] = Query(None),
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get all authors or search by name"""
        if search:
            return service.search_authors(search, limit)
        return service.get_authors(limit=limit, offset=offset)
    
    @router.get("/authors/{author_id}")
    async def get_author(
        author_id: UUID,
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get author by ID"""
        author = service.get_author_by_id(author_id)
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
        return author
    
    @router.get("/authors/{author_id}/books")
    async def get_author_books(
        author_id: UUID,
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get all books by author"""
        return service.get_books_by_author(author_id)
    
    # Book endpoints
    @router.get("/books")
    async def get_books(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        search: Optional[str] = Query(None),
        author_id: Optional[UUID] = Query(None),
        series_id: Optional[UUID] = Query(None),
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get all books with optional filtering"""
        if search:
            return service.search_books(search, limit)
        elif author_id:
            return service.get_books_by_author(author_id)
        elif series_id:
            return service.get_books_by_series(series_id)
        else:
            return service.get_books(limit=limit, offset=offset)
    
    @router.get("/books/{book_id}")
    async def get_book(
        book_id: UUID,
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get book by ID"""
        book = service.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
    
    # Series endpoints
    @router.get("/series/{series_id}")
    async def get_series(
        series_id: UUID,
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get series by ID"""
        series = service.get_series_by_id(series_id)
        if not series:
            raise HTTPException(status_code=404, detail="Series not found")
        return series
    
    @router.get("/series/{series_id}/books")
    async def get_series_books(
        series_id: UUID,
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get all books in series (ordered by series number)"""
        return service.get_books_by_series(series_id)
    
    # Request endpoints
    @router.get("/requests")
    async def get_book_requests(
        authorized_only: bool = Query(False),
        service: EbookService = Depends(get_ebook_service)
    ):
        """Get book requests"""
        return service.get_book_requests(authorized_only=authorized_only)
    
    @router.post("/requests")
    async def create_book_request(
        book_id: UUID,
        wanted_quality: str,
        min_quality: str,
        preferred_formats: str = "epub,pdf,mobi",
        service: EbookService = Depends(get_ebook_service)
    ):
        """Create a book download request"""
        return service.create_request(
            media_id=book_id,
            book_id=book_id,
            wanted_quality=wanted_quality,
            min_quality=min_quality,
            preferred_formats=preferred_formats
        )
    
    @router.post("/requests/{request_id}/authorize")
    async def authorize_book_request(
        request_id: UUID,
        user_id: UUID,
        service: EbookService = Depends(get_ebook_service)
    ):
        """Authorize a book request"""
        result = service.authorize_book_request(request_id, user_id)
        if not result:
            raise HTTPException(status_code=404, detail="Request not found")
        return result
    
    # Search and metadata endpoints
    @router.get("/search")
    async def search_metadata(
        query: str = Query(..., min_length=1),
        service: EbookService = Depends(get_ebook_service)
    ):
        """Search for books in metadata providers"""
        return service.search_metadata(query)
    
    @router.post("/add-from-metadata")
    async def add_from_metadata(
        external_id: int,
        metadata_provider: str,
        author_name: str,
        library: str = "Default",
        service: EbookService = Depends(get_ebook_service)
    ):
        """Add a book from metadata provider"""
        # Create a mock metadata result
        from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
        
        metadata_result = MetaDataProviderSearchResult(
            external_id=external_id,
            name="Sample Book",  # Would come from metadata provider
            overview="Sample description",
            year=2023,
            metadata_provider=metadata_provider,
            added=False,
            poster_path=None
        )
        
        return service.create_from_metadata(
            metadata_result,
            author_name=author_name,
            library=library
        )
    
    return router
```

## Step 6: Main Plugin Class (`plugin.py`)

```python
from typing import Type, List
from fastapi import APIRouter

from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.service import BaseMediaService
from media_manager.plugins.base.repository import BaseMediaRepository
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig
from media_manager.plugins.ebooks.models import Author, Book, Series, BookFile, BookRequest
from media_manager.plugins.ebooks.service import EbookService
from media_manager.plugins.ebooks.repository import EbookRepository
from media_manager.plugins.ebooks.router import get_ebook_router


class EbookPlugin(BaseMediaPlugin):
    """
    Ebook plugin for MediaManager
    """
    
    @property
    def plugin_info(self) -> MediaPluginInfo:
        return MediaPluginInfo(
            name="ebooks",
            display_name="Ebooks",
            version="1.0.0",
            description="Manage ebooks with automatic downloading and organization by author and series",
            media_type="ebook",
            supported_extensions=[".epub", ".pdf", ".mobi", ".azw", ".azw3", ".fb2", ".txt"],
            metadata_providers=["openlibrary", "goodreads"]
        )
    
    @property
    def media_model_class(self) -> Type[Author]:
        return Author
    
    @property
    def router(self) -> APIRouter:
        return get_ebook_router()
    
    def get_service(self, **dependencies) -> BaseMediaService:
        """Get the Ebook service instance"""
        session = dependencies.get('session')
        if not session:
            raise ValueError("Session dependency is required")
        
        repository = self.get_repository(session)
        self._service = EbookService(repository, **dependencies)
        return self._service
    
    def get_repository(self, session, **kwargs) -> BaseMediaRepository:
        """Get the Ebook repository instance"""
        self._repository = EbookRepository(session)
        return self._repository
    
    def get_database_models(self) -> List[Type]:
        """Get all database models for Ebook plugin"""
        return [Author, Book, Series, BookFile, BookRequest]
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        """Validate Ebook plugin configuration"""
        # Check that at least one library path is configured
        if not config.libraries:
            return False
        
        # Validate library paths
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
        """Called when the Ebook plugin is loaded"""
        print(f"Ebook Plugin v{self.plugin_info.version} started")
        print("Supported formats: .epub, .pdf, .mobi, .azw, .azw3, .fb2, .txt")
        print("Ready to manage your digital library!")
    
    def on_shutdown(self) -> None:
        """Called when the application shuts down"""
        print("Ebook Plugin shutting down")
```

## Step 7: Initialize Package (`__init__.py`)

```python
import logging

log = logging.getLogger(__name__)
```

## Step 8: Configuration

Add to `config.example.toml`:

```toml
# Ebooks Plugin
[media_plugins.ebooks]
enabled = false  # Set to true to enable ebook management
auto_download = true
update_metadata_interval = "monthly"  # Books don't change as often
import_check_interval = "30min"
preferred_quality = "high"  # Original > High > Medium > Low
minimum_quality = "medium"
create_subdirectories = true
file_naming_pattern = "{author}/{series}/{title}"

# Quality mappings for ebooks (based on format)
[media_plugins.ebooks.settings]
quality_mappings = { "epub" = "high", "pdf" = "medium", "mobi" = "medium", "azw3" = "high", "txt" = "low" }
preferred_formats = ["epub", "pdf", "mobi", "azw3"]
series_detection = true  # Try to detect series from metadata

[[media_plugins.ebooks.libraries]]
name = "Ebooks"
path = "/data/media/ebooks"
enabled = true

[[media_plugins.ebooks.libraries]]
name = "Audiobooks"
path = "/data/media/audiobooks"
enabled = false

[[media_plugins.ebooks.libraries]]
name = "Technical Books"
path = "/data/media/ebooks/technical"
enabled = false
```

## Step 9: Database Migration

**Important**: Each new plugin requires its own database migration when first implemented. This is expected and required for proper database schema management.

Create an Alembic migration:

```bash
uv run alembic revision --autogenerate -m "Add ebooks plugin models"
uv run alembic upgrade head
```

The plugin system automatically includes your models in the database schema, but migrations must be explicitly created and applied for each new plugin.

## Step 10: Tests

Create `tests/plugins/test_ebook_plugin.py`:

```python
import pytest
from unittest.mock import Mock
from uuid import uuid4

from media_manager.plugins.ebooks.plugin import EbookPlugin
from media_manager.plugins.ebooks.service import EbookService
from media_manager.plugins.ebooks.repository import EbookRepository
from media_manager.plugins.base.schemas import MediaPluginConfig


@pytest.fixture
def ebook_plugin():
    return EbookPlugin()


@pytest.fixture
def mock_session():
    return Mock()


def test_ebook_plugin_info(ebook_plugin):
    """Test that plugin info is correctly configured"""
    info = ebook_plugin.plugin_info
    
    assert info.name == "ebooks"
    assert info.display_name == "Ebooks"
    assert info.media_type == "ebook"
    assert ".epub" in info.supported_extensions
    assert ".pdf" in info.supported_extensions
    assert "openlibrary" in info.metadata_providers


def test_ebook_plugin_models(ebook_plugin):
    """Test that all required models are included"""
    from media_manager.plugins.ebooks.models import Author, Book, Series, BookFile, BookRequest
    
    models = ebook_plugin.get_database_models()
    assert Author in models
    assert Book in models
    assert Series in models
    assert BookFile in models
    assert BookRequest in models


def test_ebook_plugin_validate_config_valid(ebook_plugin):
    """Test validating a valid configuration"""
    config = MediaPluginConfig(
        enabled=True,
        libraries=[
            {"name": "Ebooks", "path": "/data/ebooks", "enabled": True}
        ]
    )
    
    assert ebook_plugin.validate_config(config) is True


def test_ebook_plugin_validate_config_invalid(ebook_plugin):
    """Test validating invalid configurations"""
    # No libraries
    config = MediaPluginConfig(enabled=True, libraries=[])
    assert ebook_plugin.validate_config(config) is False
    
    # Empty path
    config = MediaPluginConfig(
        enabled=True,
        libraries=[{"name": "Ebooks", "path": "", "enabled": True}]
    )
    assert ebook_plugin.validate_config(config) is False


def test_ebook_service_methods():
    """Test ebook service functionality"""
    mock_repo = Mock(spec=EbookRepository)
    service = EbookService(repository=mock_repo)
    
    # Test plugin info
    info = service.get_plugin_info()
    assert info.name == "ebooks"
    
    # Test search methods
    service.search_books("test")
    mock_repo.search_books_by_title.assert_called_with("test", 20)
    
    service.search_authors("author")
    mock_repo.search_authors_by_name.assert_called_with("author", 20)


def test_ebook_repository_methods(mock_session):
    """Test ebook repository functionality"""
    repo = EbookRepository(mock_session)
    
    # Test that it's properly initialized
    assert repo.session == mock_session
    assert repo.model_class.__name__ == "Author"


# Add more comprehensive tests for all components
```

## Step 11: Enable and Test

1. **Enable in configuration**:
   ```toml
   [media_plugins.ebooks]
   enabled = true
   ```

2. **Run database migration**:
   ```bash
   uv run alembic upgrade head
   ```

3. **Start MediaManager**:
   ```bash
   uv run uvicorn media_manager.main:app --reload
   ```

4. **Test API endpoints**:
   ```bash
   # Check plugin is loaded
   curl http://localhost:8000/api/v1/plugins
   
   # Test ebook endpoints
   curl http://localhost:8000/api/v1/ebooks/authors
   curl http://localhost:8000/api/v1/ebooks/books
   ```

## Key Features of This Implementation

### 1. **Hierarchical Structure**
- Authors → Books (one-to-many)
- Series → Books (one-to-many, optional)
- Books can belong to both an author and a series

### 2. **Comprehensive Metadata**
- ISBN/ISBN13 support
- Publisher and publication date
- Language and page count
- Genre classification

### 3. **Series Support**
- Books can be part of a series
- Series numbering for proper ordering
- Series completion tracking

### 4. **Format-Aware Quality**
- Different quality levels based on file format
- Format preferences (epub > pdf > mobi)
- Multiple formats per book

### 5. **Rich Search and Filtering**
- Search by title, author, or series
- Filter books by author or series
- Pagination support

### 6. **Request System**
- Quality preferences
- Format preferences
- Authorization workflow

This complete example demonstrates how to create a sophisticated plugin that handles complex relationships and provides a rich API for managing ebooks. The same patterns can be applied to any media type you want to add to MediaManager.