"""Real-Debrid API Client.

Real-Debrid is a popular unrestricted downloader service providing cached torrent downloads.
API Docs: https://api.real-debrid.com/

Note: RD requires rate limiting (429 errors) and has deprecated cache detection endpoints,
we must add/select/check torrents to determine cache status.
"""
import logging
import threading
import time
from pathlib import Path

import httpx

from media_manager.debrid.schemas import (
    DebridCacheStatus,
    DebridTorrentInfo,
    DebridFile,
    DebridDirectLink,
    DebridError,
    DebridProvider,
    DebridProviderInfo,
)

log = logging.getLogger(__name__)

BASE_URL = "https://api.real-debrid.com/rest/1.0"
RATE_LIMIT_SECONDS = 0.25


class RealDebridClient:
    """Client for Real-Debrid API with built-in rate limiting."""

    # Class-level rate limiting shared across all instances
    _lock = threading.Lock()
    _last_request_time = 0.0

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def get_info(self) -> DebridProviderInfo:
        """Return provider metadata."""
        return DebridProviderInfo(
            id=DebridProvider.RealDebrid,
            name="Real-Debrid",
            description="Popular unrestricted downloader service",
            website="https://real-debrid.com",
            color="blue",
            is_implemented=True,
            supports_cache_check=True,
            rate_limit_seconds=0.50,
        )

    def check_cache(self, hash_str: str) -> DebridCacheStatus:
        """
        Check if torrent is cached on Real-Debrid.

        RD has no dedicated cache endpoint, so we add the magnet, select files,
        and check if status becomes 'downloaded' instantly (cached).
        Uncached torrents are deleted after check.
        """
        magnet = f"magnet:?xt=urn:btih:{hash_str}"

        try:
            # Check if already exists
            existing_id = self.find_torrent_by_hash(hash_str)
            if existing_id:
                info = self._get_raw_torrent_info(existing_id)
                if info.get("status") == "downloaded":
                    return self._build_cache_status(info, hash_str, is_cached=True)

                torrent_id = existing_id
            else:
                torrent_id = self._add_magnet_raw(magnet)

            # Selecting files triggers cache check
            self._select_all_files(torrent_id)
            info = self._get_raw_torrent_info(torrent_id)
            is_cached = info.get("status") == "downloaded"

            # Clean up if we created it
            if not existing_id:
                self._delete_torrent(torrent_id)

            return self._build_cache_status(info, hash_str, is_cached)

        except DebridError:
            raise
        except Exception as e:
            raise DebridError(f"Cache check failed: {e}")

    def add_magnet(self, magnet: str) -> str:
        """Add magnet link and return torrent ID."""
        try:
            hash_str = self._extract_hash(magnet)
            if hash_str:
                existing_id = self.find_torrent_by_hash(hash_str)
                if existing_id:
                    log.info(f"Real-Debrid: Torrent already exists: {existing_id}")
                    return existing_id

            torrent_id = self._add_magnet_raw(magnet)
            self._select_all_files(torrent_id)

            log.info(f"Real-Debrid: Added torrent {torrent_id}")
            return torrent_id

        except DebridError:
            raise
        except Exception as e:
            raise DebridError(f"Failed to add magnet: {e}")

    def get_torrent_info(self, torrent_id: str) -> DebridTorrentInfo | None:
        """Get torrent details including file list."""
        try:
            data = self._get_raw_torrent_info(torrent_id)
            if not data:
                return None

            files = [
                DebridFile(
                    id=str(f["id"]),
                    name=f["path"],
                    short_name=f["path"].rsplit("/", 1)[-1],
                    size=f["bytes"],
                )
                for f in data.get("files") or []
                if f.get("selected", 0) == 1
            ]

            return DebridTorrentInfo(
                id=torrent_id,
                name=data.get("filename", ""),
                size=data.get("bytes", 0),
                hash=data.get("hash", ""),
                files=files,
            )

        except DebridError:
            return None
        except Exception as e:
            log.warning(f"Real-Debrid: Failed to get torrent info: {e}")
            return None

    def get_download_link(self, torrent_id: str, file_id: str, filename: str, size: int) -> DebridDirectLink:
        """Get direct download URL for a file."""
        try:
            data = self._get_raw_torrent_info(torrent_id)

            if data.get("status") != "downloaded":
                raise DebridError(f"Torrent not ready, status: {data.get('status')}")

            links = data.get("links", [])
            if not links:
                raise DebridError("No links available for torrent")

            link = self._match_file_to_link(data, file_id, links)
            return self._unrestrict_link(link)

        except DebridError:
            raise
        except Exception as e:
            raise DebridError(f"Failed to get download link: {e}")

    def download_file(self, torrent_id: str, file_id: str, destination: str) -> str:
        """Stream file to local path. Returns actual path (RD may rename files)."""
        try:
            link = self.get_download_link(torrent_id, file_id, "", 0)

            # RD returns actual filename which may differ (e.g., .rar vs .mkv)
            actual_filename = link.filename
            dest_dir = Path(destination).parent
            actual_destination = dest_dir / actual_filename

            log.info(f"Real-Debrid: Downloading to {actual_destination}")
            with self.client.stream("GET", link.url, timeout=None) as response:
                response.raise_for_status()
                with open(actual_destination, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)

            log.info(f"Real-Debrid: Download complete: {actual_destination}")
            return str(actual_destination)

        except Exception as e:
            raise DebridError(f"Download failed: {e}")

    def delete_torrent(self, torrent_id: str) -> None:
        """Delete torrent from Real-Debrid."""
        self._delete_torrent(torrent_id)

    def find_torrent_by_hash(self, hash_str: str) -> str | None:
        """Find existing torrent by hash, returns torrent ID or None."""
        try:
            self._rate_limit()
            response = self.client.get("/torrents")
            if not response.is_success:
                return None

            target_hash = hash_str.lower()
            for torrent in response.json():
                if torrent.get("hash", "").lower() == target_hash:
                    return torrent["id"]
        except Exception:
            pass
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Private: API calls
    # ─────────────────────────────────────────────────────────────────────────

    def _add_magnet_raw(self, magnet: str) -> str:
        """Add magnet without file selection."""
        self._rate_limit()
        response = self.client.post("/torrents/addMagnet", data={"magnet": magnet})

        if not response.is_success:
            raise self._handle_error(response.status_code, response.text)

        return response.json()["id"]

    def _select_all_files(self, torrent_id: str) -> None:
        """Select all files - required before RD starts processing."""
        self._rate_limit()
        response = self.client.post(f"/torrents/selectFiles/{torrent_id}", data={"files": "all"})

        if response.status_code not in (200, 201, 204):
            raise self._handle_error(response.status_code, response.text)

        log.debug(f"Real-Debrid: Selected all files for {torrent_id}")

    def _get_raw_torrent_info(self, torrent_id: str) -> dict:
        """Get raw torrent info from API."""
        self._rate_limit()
        response = self.client.get(f"/torrents/info/{torrent_id}")

        if not response.is_success:
            raise self._handle_error(response.status_code, response.text)

        return response.json()

    def _delete_torrent(self, torrent_id: str) -> None:
        """Delete torrent from Real-Debrid."""
        self._rate_limit()
        response = self.client.delete(f"/torrents/delete/{torrent_id}")

        if response.status_code not in (200, 204):
            log.warning(f"Real-Debrid: Failed to delete torrent {torrent_id}")

    def _unrestrict_link(self, link: str) -> DebridDirectLink:
        """Convert hoster link to direct download URL."""
        self._rate_limit()
        response = self.client.post("/unrestrict/link", data={"link": link})

        if not response.is_success:
            raise self._handle_error(response.status_code, response.text)

        data = response.json()
        return DebridDirectLink(
            url=data["download"],
            filename=data["filename"],
            size=data["filesize"],
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Private: Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Enforce minimum delay between API calls to avoid 429 errors."""
        with RealDebridClient._lock:
            now = time.time()
            elapsed = now - RealDebridClient._last_request_time
            if elapsed < RATE_LIMIT_SECONDS:
                time.sleep(RATE_LIMIT_SECONDS - elapsed)
            RealDebridClient._last_request_time = time.time()

    def _handle_error(self, status_code: int, error_text: str) -> DebridError:
        """Convert HTTP error to DebridError."""
        if status_code in (401, 403):
            return DebridError("Invalid or expired API key", code="invalid_api_key")
        elif status_code == 429:
            return DebridError("Rate limited by Real-Debrid", code="rate_limited")
        return DebridError(f"API error {status_code}: {error_text}")

    def _build_cache_status(self, info: dict, hash_str: str, is_cached: bool) -> DebridCacheStatus:
        """Build cache status response."""
        return DebridCacheStatus(
            is_cached=is_cached,
            provider=DebridProvider.RealDebrid,
            name=info.get("filename") if is_cached else None,
            size=info.get("bytes") if is_cached else None,
            hash=info.get("hash", hash_str),
        )

    def _match_file_to_link(self, data: dict, file_id: str, links: list) -> str:
        """Match file ID to download link (RD links are positional)."""
        selected_files = [f for f in data.get("files", []) if f.get("selected") == 1]
        file_id_num = int(file_id)

        link_index = next(
            (i for i, f in enumerate(selected_files) if f["id"] == file_id_num),
            None,
        )

        if link_index is not None and link_index < len(links):
            return links[link_index]

        # Fallback: files may be archived together, use first link
        if links:
            return links[0]

        raise DebridError("Could not find download link for file")

    def _extract_hash(self, magnet: str) -> str | None:
        """Extract info hash from magnet link."""
        if "btih:" not in magnet:
            return None

        start = magnet.find("btih:") + 5
        end = magnet.find("&", start)
        return magnet[start:end if end != -1 else None].lower()
