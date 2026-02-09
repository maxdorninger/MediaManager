import logging
import time
from typing import override

import requests

from media_manager.books.schemas import Author, Book, BookFormat
from media_manager.metadataProvider.abstract_book_metadata_provider import (
    AbstractBookMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.notification.manager import notification_manager

log = logging.getLogger(__name__)

# Cache: author_olid -> (cover_art_url, timestamp). TTL = 1 week.
_cover_art_cache: dict[str, tuple[str | None, float]] = {}
_COVER_ART_CACHE_TTL = 604800

_REQUEST_DELAY = 0.1  # seconds between API calls to be respectful


class OpenLibraryMetadataProvider(AbstractBookMetadataProvider):
    name = "openlibrary"

    @staticmethod
    def __get_author_cover_art_url(author_olid: str) -> str | None:
        """Get a cover art URL for an author from OpenLibrary.

        Results are cached in memory for 1 week.
        """
        cached = _cover_art_cache.get(author_olid)
        if cached and (time.monotonic() - cached[1]) < _COVER_ART_CACHE_TTL:
            return cached[0]

        url = f"https://covers.openlibrary.org/a/olid/{author_olid}-L.jpg?default=false"
        try:
            resp = requests.head(url, timeout=5, allow_redirects=True)
            if resp.status_code == 200:
                _cover_art_cache[author_olid] = (url, time.monotonic())
                return url
        except requests.RequestException:
            log.debug(f"Failed to check cover art for author {author_olid}")

        _cover_art_cache[author_olid] = (None, time.monotonic())
        return None

    def __enrich_with_cover_art(
        self, results: list[MetaDataProviderSearchResult], max_new_lookups: int = 6
    ) -> None:
        """Fetch cover art URLs for results.

        Cached lookups are free. New lookups are capped at `max_new_lookups`
        to keep response times reasonable.
        """
        new_lookups = 0
        for result in results:
            olid = str(result.external_id)
            is_cached = olid in _cover_art_cache and (
                time.monotonic() - _cover_art_cache[olid][1]
            ) < _COVER_ART_CACHE_TTL
            if not is_cached and new_lookups >= max_new_lookups:
                continue
            if not is_cached:
                new_lookups += 1
            url = self.__get_author_cover_art_url(olid)
            if url:
                result.poster_path = url

    @override
    def search_author(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        if query is None:
            return self.__get_trending_authors()

        try:
            response = requests.get(
                url="https://openlibrary.org/search/authors.json",
                params={"q": query, "limit": 25},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            log.exception(f"OpenLibrary API error searching authors with query '{query}'")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="OpenLibrary API Error",
                    message=f"Failed to search authors with query '{query}'. Error: {e}",
                )
            raise

        formatted_results = []
        for author in data.get("docs", []):
            try:
                author_key = author.get("key", "")
                name = author.get("name", "Unknown Author")
                top_work = author.get("top_work", "")
                work_count = author.get("work_count", 0)
                birth_date = author.get("birth_date", "")

                overview_parts = []
                if top_work:
                    overview_parts.append(f"Top work: {top_work}")
                if work_count:
                    overview_parts.append(f"{work_count} works")
                if birth_date:
                    overview_parts.append(f"Born: {birth_date}")
                overview = " | ".join(overview_parts) if overview_parts else None

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=None,
                        overview=overview,
                        name=name,
                        external_id=author_key,
                        year=None,
                        metadata_provider=self.name,
                        added=False,
                        vote_average=None,
                        original_language=None,
                    )
                )
            except Exception:
                log.warning("Error processing OpenLibrary search result", exc_info=True)

        self.__enrich_with_cover_art(formatted_results)

        return formatted_results

    def __get_trending_authors(self) -> list[MetaDataProviderSearchResult]:
        """Fetch trending/popular works from OpenLibrary and extract unique authors."""
        try:
            response = requests.get(
                url="https://openlibrary.org/trending/daily.json",
                params={"limit": 25},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            log.exception("OpenLibrary API error getting trending works")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="OpenLibrary API Error",
                    message=f"Failed to fetch trending works from OpenLibrary. Error: {e}",
                )
            return []

        seen_authors: set[str] = set()
        formatted_results = []
        for work in data.get("works", []):
            try:
                authors = work.get("authors", []) or work.get("author_name", [])
                if not authors:
                    continue

                # Handle both formats
                if isinstance(authors[0], dict):
                    author_key = authors[0].get("key", "").replace("/authors/", "")
                    author_name = authors[0].get("name", "Unknown Author")
                else:
                    author_keys = work.get("author_key", [])
                    if not author_keys:
                        continue
                    author_key = author_keys[0]
                    author_name = authors[0]

                if not author_key or author_key in seen_authors:
                    continue
                seen_authors.add(author_key)

                title = work.get("title", "")
                overview = f"Trending: {title}" if title else None

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=None,
                        overview=overview,
                        name=author_name,
                        external_id=author_key,
                        year=None,
                        metadata_provider=self.name,
                        added=False,
                        vote_average=None,
                        original_language=None,
                    )
                )
            except Exception:
                log.warning("Error processing OpenLibrary trending result", exc_info=True)

        self.__enrich_with_cover_art(formatted_results)

        return formatted_results

    @override
    def search_book(self, query: str) -> list[MetaDataProviderSearchResult]:
        try:
            response = requests.get(
                url="https://openlibrary.org/search.json",
                params={"q": query, "limit": 25},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            log.exception(f"OpenLibrary API error searching books with query '{query}'")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="OpenLibrary API Error",
                    message=f"Failed to search books with query '{query}'. Error: {e}",
                )
            raise

        formatted_results = []
        for doc in data.get("docs", []):
            try:
                work_key = doc.get("key", "").replace("/works/", "")
                title = doc.get("title", "Unknown Book")
                author_names = doc.get("author_name", [])
                year = doc.get("first_publish_year")

                overview = ", ".join(author_names) if author_names else None

                cover_id = doc.get("cover_i")
                poster_path = (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                    if cover_id
                    else None
                )

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_path,
                        overview=overview,
                        name=title,
                        external_id=work_key,
                        year=year,
                        metadata_provider=self.name,
                        added=False,
                        vote_average=None,
                        original_language=None,
                    )
                )
            except Exception:
                log.warning("Error processing OpenLibrary book search result", exc_info=True)

        return formatted_results

    @override
    def get_author_metadata(self, author_id: str) -> Author:
        try:
            response = requests.get(
                url=f"https://openlibrary.org/authors/{author_id}.json",
                timeout=15,
            )
            response.raise_for_status()
            author_data = response.json()
        except requests.RequestException as e:
            log.exception(f"OpenLibrary API error getting author metadata for ID {author_id}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="OpenLibrary API Error",
                    message=f"Failed to fetch author metadata for ID {author_id}. Error: {e}",
                )
            raise

        time.sleep(_REQUEST_DELAY)

        # Fetch author's works
        books = []
        try:
            works_response = requests.get(
                url=f"https://openlibrary.org/authors/{author_id}/works.json",
                params={"limit": 100},
                timeout=15,
            )
            works_response.raise_for_status()
            works_data = works_response.json()

            for work in works_data.get("entries", []):
                work_key = work.get("key", "").replace("/works/", "")
                title = work.get("title", "Unknown Work")

                # Try to get year from created date
                year = None
                if work.get("first_publish_date"):
                    try:
                        year = int(str(work["first_publish_date"])[:4])
                    except (ValueError, IndexError):
                        pass

                # Determine format based on subjects
                book_format = BookFormat.ebook

                books.append(
                    Book(
                        external_id=work_key,
                        name=title,
                        year=year,
                        format=book_format,
                    )
                )
        except requests.RequestException:
            log.warning(
                f"Failed to fetch works for author {author_id}", exc_info=True
            )

        # Sort books by year
        books.sort(key=lambda b: b.year or 9999)

        # Build overview
        bio = author_data.get("bio")
        if isinstance(bio, dict):
            overview = bio.get("value", "")
        elif isinstance(bio, str):
            overview = bio
        else:
            overview = ""

        birth_date = author_data.get("birth_date", "")
        death_date = author_data.get("death_date", "")
        if birth_date:
            life_info = f"Born: {birth_date}"
            if death_date:
                life_info += f" - Died: {death_date}"
            overview = f"{life_info}. {overview}" if overview else life_info

        return Author(
            external_id=author_id,
            name=author_data.get("name", "Unknown Author"),
            overview=overview or "",
            metadata_provider=self.name,
            books=books,
        )

    @override
    def download_author_cover_image(self, author: Author) -> bool:
        """Download cover art for the author from OpenLibrary."""
        author_olid = author.external_id
        url = f"https://covers.openlibrary.org/a/olid/{author_olid}-L.jpg?default=false"

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200 or len(resp.content) < 1000:
                # Try first book's cover instead
                for book in author.books:
                    book_url = f"https://covers.openlibrary.org/b/olid/{book.external_id}-L.jpg?default=false"
                    try:
                        book_resp = requests.get(book_url, timeout=15)
                        if book_resp.status_code == 200 and len(book_resp.content) >= 1000:
                            resp = book_resp
                            break
                    except requests.RequestException:
                        continue
                else:
                    log.warning(f"No cover art found for author {author.name}")
                    return False
        except requests.RequestException:
            log.warning(f"Failed to download cover art for author {author.name}", exc_info=True)
            return False

        try:
            image_file_path = self.storage_path / f"{author.id}.jpg"
            image_file_path.write_bytes(resp.content)

            from PIL import Image

            original_image = Image.open(image_file_path)
            original_image.save(
                image_file_path.with_suffix(".avif"), quality=50
            )
            original_image.save(
                image_file_path.with_suffix(".webp"), quality=50
            )
            log.info(f"Successfully downloaded cover image for author {author.name}")
            return True
        except Exception:
            log.warning(
                f"Failed to process cover image for author {author.name}",
                exc_info=True,
            )
            return False

    @override
    def download_book_cover_image(self, book: Book) -> bool:
        """Download cover art for a book from OpenLibrary."""
        url = f"https://covers.openlibrary.org/b/olid/{book.external_id}-L.jpg?default=false"

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200 or len(resp.content) < 1000:
                log.warning(f"No cover art found for book {book.name}")
                return False
        except requests.RequestException:
            log.warning(f"Failed to download cover art for book {book.name}", exc_info=True)
            return False

        try:
            image_file_path = self.storage_path / f"{book.id}.jpg"
            image_file_path.write_bytes(resp.content)

            from PIL import Image

            original_image = Image.open(image_file_path)
            original_image.save(
                image_file_path.with_suffix(".avif"), quality=50
            )
            original_image.save(
                image_file_path.with_suffix(".webp"), quality=50
            )
            log.info(f"Successfully downloaded cover image for book {book.name}")
            return True
        except Exception:
            log.warning(
                f"Failed to process cover image for book {book.name}",
                exc_info=True,
            )
            return False
