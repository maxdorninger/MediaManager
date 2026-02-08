import logging
import time
from typing import override

import musicbrainzngs
import requests

import media_manager.metadataProvider.utils
from media_manager.metadataProvider.abstract_music_metadata_provider import (
    AbstractMusicMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.music.schemas import Album, Artist, Track
from media_manager.notification.manager import notification_manager

log = logging.getLogger(__name__)

# MusicBrainz requires a user agent string
musicbrainzngs.set_useragent("MediaManager", "0.1.0", "https://github.com/maxdorninger/MediaManager")

# Cache: artist_mbid -> (cover_art_url, timestamp). TTL = 1 week.
_cover_art_cache: dict[str, tuple[str | None, float]] = {}
_COVER_ART_CACHE_TTL = 604800

# Cache the full trending response so repeated dashboard loads are instant.
# TTL = 1 hour (trending data changes slowly).
_trending_cache: tuple[list[MetaDataProviderSearchResult], float] | None = None
_TRENDING_CACHE_TTL = 3600


class MusicBrainzMetadataProvider(AbstractMusicMetadataProvider):
    name = "musicbrainz"

    @staticmethod
    def __get_artist_cover_art_url(artist_mbid: str) -> str | None:
        """Get a cover art URL for an artist by finding their first album.

        Results are cached in memory for 1 week to avoid repeated
        MusicBrainz API calls (rate-limited to 1 req/sec).
        """
        cached = _cover_art_cache.get(artist_mbid)
        if cached and (time.monotonic() - cached[1]) < _COVER_ART_CACHE_TTL:
            return cached[0]

        url = None
        try:
            result = musicbrainzngs.browse_release_groups(
                artist=artist_mbid, release_type=["album"], limit=1
            )
            release_groups = result.get("release-group-list", [])
            if release_groups:
                rg_id = release_groups[0]["id"]
                url = f"https://coverartarchive.org/release-group/{rg_id}/front-250"
        except musicbrainzngs.WebServiceError:
            log.debug(f"Failed to get release group for artist {artist_mbid}")

        _cover_art_cache[artist_mbid] = (url, time.monotonic())
        return url

    def __get_trending_artists(self) -> list[MetaDataProviderSearchResult]:
        """Fetch trending artists from the ListenBrainz sitewide statistics API.

        The full enriched result is cached for 1 hour so repeated
        dashboard loads are instant after the first request.
        """
        global _trending_cache
        if _trending_cache and (time.monotonic() - _trending_cache[1]) < _TRENDING_CACHE_TTL:
            # Re-enrich on cache hit: cover art lookups that were skipped
            # (due to max_new_lookups) on the first call can now be filled in
            # progressively — already-cached URLs are free hits.
            self.__enrich_with_cover_art(_trending_cache[0])
            # Return deep copies so the service layer can mutate (e.g. set added=True)
            # without affecting the cache
            return [r.model_copy() for r in _trending_cache[0]]

        try:
            response = requests.get(
                url="https://api.listenbrainz.org/1/stats/sitewide/artists",
                params={"count": 25, "range": "this_week"},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            log.exception("ListenBrainz API error getting trending artists")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="ListenBrainz API Error",
                    message=f"Failed to fetch trending artists from ListenBrainz. Error: {e}",
                )
            return []

        formatted_results = []
        for artist in data.get("payload", {}).get("artists", []):
            try:
                artist_mbid = artist.get("artist_mbid")
                if not artist_mbid:
                    continue

                listen_count = artist.get("listen_count", 0)
                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=None,
                        overview=f"{listen_count:,} listens this week",
                        name=artist.get("artist_name", "Unknown Artist"),
                        external_id=artist_mbid,
                        year=None,
                        metadata_provider=self.name,
                        added=False,
                        vote_average=None,
                        original_language=None,
                    )
                )
            except Exception:
                log.warning("Error processing ListenBrainz trending result", exc_info=True)

        self.__enrich_with_cover_art(formatted_results)

        _trending_cache = (formatted_results, time.monotonic())

        return [r.model_copy() for r in formatted_results]

    def __enrich_with_cover_art(
        self, results: list[MetaDataProviderSearchResult], max_new_lookups: int = 6
    ) -> None:
        """Fetch cover art URLs for results.

        Cached lookups are free. New MusicBrainz lookups are rate-limited
        to 1 req/sec, so we cap uncached lookups at `max_new_lookups` to
        keep response times reasonable.
        """
        new_lookups = 0
        for result in results:
            mbid = str(result.external_id)
            is_cached = mbid in _cover_art_cache and (
                time.monotonic() - _cover_art_cache[mbid][1]
            ) < _COVER_ART_CACHE_TTL
            if not is_cached and new_lookups >= max_new_lookups:
                continue
            if not is_cached:
                new_lookups += 1
            url = self.__get_artist_cover_art_url(mbid)
            if url:
                result.poster_path = url

    @override
    def search_artist(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        if query is None:
            return self.__get_trending_artists()

        try:
            result = musicbrainzngs.search_artists(artist=query, limit=25)
        except musicbrainzngs.WebServiceError as e:
            log.exception(f"MusicBrainz API error searching artists with query '{query}'")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="MusicBrainz API Error",
                    message=f"Failed to search artists with query '{query}'. Error: {e}",
                )
            raise

        formatted_results = []
        for artist in result.get("artist-list", []):
            try:
                artist_id = artist["id"]
                name = artist.get("name", "Unknown Artist")
                disambiguation = artist.get("disambiguation", "")
                country = artist.get("country", "")

                overview = disambiguation
                if country:
                    overview = f"{country} - {disambiguation}" if disambiguation else country

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=None,
                        overview=overview or None,
                        name=name,
                        external_id=artist_id,
                        year=None,
                        metadata_provider=self.name,
                        added=False,
                        vote_average=int(artist.get("ext:score", 0)) / 10.0
                        if artist.get("ext:score")
                        else None,
                        original_language=None,
                    )
                )
            except Exception:
                log.warning("Error processing MusicBrainz search result", exc_info=True)

        self.__enrich_with_cover_art(formatted_results)

        return formatted_results

    @override
    def get_artist_metadata(self, artist_id: str) -> Artist:
        try:
            mb_artist = musicbrainzngs.get_artist_by_id(
                artist_id, includes=["release-groups"]
            )["artist"]
        except musicbrainzngs.WebServiceError as e:
            log.exception(f"MusicBrainz API error getting artist metadata for ID {artist_id}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="MusicBrainz API Error",
                    message=f"Failed to fetch artist metadata for ID {artist_id}. Error: {e}",
                )
            raise

        albums = []
        for rg in mb_artist.get("release-group-list", []):
            rg_type = rg.get("type", "Other")
            if rg_type.lower() not in {"album", "single", "ep", "compilation"}:
                continue

            # Get year from first-release-date
            year = media_manager.metadataProvider.utils.get_year_from_date(
                rg.get("first-release-date")
            )

            tracks = self.__get_release_group_tracks(rg["id"])

            albums.append(
                Album(
                    external_id=rg["id"],
                    name=rg.get("title", "Unknown Album"),
                    year=year,
                    album_type=rg_type.lower(),
                    tracks=tracks,
                )
            )

        # Sort albums by year
        albums.sort(key=lambda a: a.year or 9999)

        overview = mb_artist.get("disambiguation", "")
        life_span = mb_artist.get("life-span", {})
        if life_span.get("begin"):
            active_since = f"Active since {life_span['begin']}"
            if life_span.get("ended", "false") == "true" and life_span.get("end"):
                active_since += f" - {life_span['end']}"
            overview = f"{active_since}. {overview}" if overview else active_since

        return Artist(
            external_id=artist_id,
            name=mb_artist.get("name", "Unknown Artist"),
            overview=overview or "",
            metadata_provider=self.name,
            country=mb_artist.get("country"),
            disambiguation=mb_artist.get("disambiguation"),
            albums=albums,
        )

    def __get_release_group_tracks(self, release_group_id: str) -> list[Track]:
        """Get tracks from a release group by finding the best release within it."""
        try:
            result = musicbrainzngs.browse_releases(
                release_group=release_group_id,
                includes=["recordings"],
                limit=1,
            )
        except musicbrainzngs.WebServiceError:
            log.warning(
                f"Failed to get tracks for release group {release_group_id}",
                exc_info=True,
            )
            return []

        releases = result.get("release-list", [])
        if not releases:
            return []

        release = releases[0]
        tracks = []
        for medium in release.get("medium-list", []):
            for track_data in medium.get("track-list", []):
                recording = track_data.get("recording", {})
                # Use a running counter to ensure unique numbers across multi-disc releases
                tracks.append(
                    Track(
                        external_id=recording.get("id", track_data.get("id", "")),
                        title=recording.get("title", track_data.get("title", "Unknown Track")),
                        number=len(tracks) + 1,
                        duration_ms=int(recording["length"])
                        if recording.get("length")
                        else None,
                    )
                )

        return tracks

    @override
    def download_artist_cover_image(self, artist: Artist) -> bool:
        """Download cover art for the artist's first album from Cover Art Archive."""
        for album in artist.albums:
            try:
                image_data = musicbrainzngs.get_release_group_image_front(
                    album.external_id
                )
            except musicbrainzngs.ResponseError:
                continue
            except musicbrainzngs.WebServiceError:
                log.warning(
                    f"Failed to download cover art for album {album.name}",
                    exc_info=True,
                )
                continue

            if image_data:
                try:
                    image_file_path = self.storage_path / f"{artist.id}.jpg"
                    image_file_path.write_bytes(image_data)

                    from PIL import Image

                    original_image = Image.open(image_file_path)
                    original_image.save(
                        image_file_path.with_suffix(".avif"), quality=50
                    )
                    original_image.save(
                        image_file_path.with_suffix(".webp"), quality=50
                    )
                    log.info(f"Successfully downloaded cover image for artist {artist.name}")
                    return True
                except Exception:
                    log.warning(
                        f"Failed to process cover image for artist {artist.name}",
                        exc_info=True,
                    )
                    continue

        log.warning(f"No cover art found for artist {artist.name}")
        return False
