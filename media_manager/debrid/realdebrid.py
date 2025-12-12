"""Real-Debrid API Client."""
import logging
import httpx
import threading
import time
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

# Rate limit: minimum seconds between RD API calls
RD_RATE_LIMIT_SECONDS = 0.25


class RealDebridClient:
    # Class-level rate limiting to avoid 429 errors
    _lock = threading.Lock()
    _last_request_time = 0.0

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )
    
    def _rate_limit(self):
        with RealDebridClient._lock:
            now = time.time()
            elapsed = now - RealDebridClient._last_request_time
            if elapsed < RD_RATE_LIMIT_SECONDS:
                time.sleep(RD_RATE_LIMIT_SECONDS - elapsed)
            RealDebridClient._last_request_time = time.time()

    def get_info(self) -> DebridProviderInfo:
        return DebridProviderInfo(
            id=DebridProvider.RealDebrid,
            name="Real-Debrid",
            description="Popular unrestricted downloader service",
            website="https://real-debrid.com",
            color="blue",
            is_implemented=True,
            supports_cache_check=True,
            returns_archives=True,
            rate_limit_seconds=0.25,
        )

    def _handle_error(self, status_code: int, error_text: str) -> DebridError:
        if status_code in (401, 403):
            return DebridError("Invalid or expired API key", code="invalid_api_key")
        elif status_code == 429:
            return DebridError("Rate limited by Real-Debrid", code="rate_limited")
        else:
            return DebridError(f"API error {status_code}: {error_text}")

    def check_cache(self, hash_str: str) -> DebridCacheStatus:
        """
        RD lacks a cache check endpoint, so we add the magnet, select files,
        and check if status becomes 'downloaded' instantly (cached) or not.
        Cached torrents are kept for download; uncached are deleted.
        """
        magnet = f"magnet:?xt=urn:btih:{hash_str}"
        
        try:
            existing_id = self._find_existing_torrent(hash_str)
            if existing_id:
                torrent_id = existing_id
                info = self._get_raw_torrent_info(torrent_id)
                if info.get("status") == "downloaded":
                    return DebridCacheStatus(
                        is_cached=True,
                        provider=DebridProvider.RealDebrid,
                        name=info.get("filename"),
                        size=info.get("bytes"),
                        hash=info.get("hash", hash_str)
                    )
            else:
                torrent_id = self._add_magnet_raw(magnet)
            
            # File selection triggers RD to check cache - status becomes 'downloaded' if cached
            self._select_all_files(torrent_id)
            
            info = self._get_raw_torrent_info(torrent_id)
            is_cached = info.get("status") == "downloaded"
            
            if is_cached:
                return DebridCacheStatus(
                    is_cached=True,
                    provider=DebridProvider.RealDebrid,
                    name=info.get("filename"),
                    size=info.get("bytes"),
                    hash=info.get("hash", hash_str)
                )
            else:
                self._delete_torrent(torrent_id)
                return DebridCacheStatus(
                    is_cached=False,
                    provider=DebridProvider.RealDebrid,
                    name=None,
                    size=None,
                    hash=hash_str
                )
                
        except DebridError:
            raise
        except Exception as e:
            raise DebridError(f"Cache check failed: {e}")

    def add_magnet(self, magnet: str) -> str:
        try:
            hash_str = self._extract_hash(magnet)
            if hash_str:
                existing_id = self._find_existing_torrent(hash_str)
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

    def _add_magnet_raw(self, magnet: str) -> str:
        """Add magnet without file selection."""
        self._rate_limit()
        response = self.client.post(
            "/torrents/addMagnet",
            data={"magnet": magnet}
        )
        
        if not response.is_success:
            raise self._handle_error(response.status_code, response.text)
        
        data = response.json()
        return data["id"]

    def _select_all_files(self, torrent_id: str) -> None:
        """RD requires file selection before torrent processing begins."""
        self._rate_limit()
        response = self.client.post(
            f"/torrents/selectFiles/{torrent_id}",
            data={"files": "all"}
        )
        
        # 204 No Content is success
        if response.status_code not in (200, 201, 204):
            raise self._handle_error(response.status_code, response.text)
        
        log.debug(f"Real-Debrid: Selected all files for {torrent_id}")

    def _delete_torrent(self, torrent_id: str) -> None:
        """Delete a torrent from Real-Debrid."""
        self._rate_limit()
        response = self.client.delete(f"/torrents/delete/{torrent_id}")
        
        # 204 No Content is success
        if response.status_code not in (200, 204):
            log.warning(f"Real-Debrid: Failed to delete torrent {torrent_id}")

    def _get_raw_torrent_info(self, torrent_id: str) -> dict:
        """Get raw torrent info from API."""
        self._rate_limit()
        response = self.client.get(f"/torrents/info/{torrent_id}")
        
        if not response.is_success:
            raise self._handle_error(response.status_code, response.text)
        
        return response.json()

    def get_torrent_info(self, torrent_id: str) -> DebridTorrentInfo | None:
        """Get torrent info with file list."""
        try:
            data = self._get_raw_torrent_info(torrent_id)
            if data is None:
                return None
            
            files = [
                DebridFile(
                    id=str(f["id"]),
                    name=f["path"],
                    short_name=f["path"].rsplit("/", 1)[-1],
                    size=f["bytes"]
                )
                for f in data.get("files") or []
                if f.get("selected", 0) == 1
            ]
            
            return DebridTorrentInfo(
                id=torrent_id,
                name=data.get("filename", ""),
                size=data.get("bytes", 0),
                hash=data.get("hash", ""),
                files=files
            )
            
        except DebridError:
            return None
        except Exception as e:
            log.warning(f"RealDebrid: Failed to get torrent info: {e}")
            return None

    def get_download_link(self, torrent_id: str, file_id: str, filename: str, size: int) -> DebridDirectLink:
        """Get direct download link for a file."""
        try:
            data = self._get_raw_torrent_info(torrent_id)
            
            if data.get("status") != "downloaded":
                raise DebridError(f"Torrent not ready, status: {data.get('status')}")
            
            links = data.get("links", [])
            if not links:
                raise DebridError("No links available for torrent")
            
            # Match file to link by position
            selected_files = [f for f in data.get("files", []) if f.get("selected") == 1]
            file_id_num = int(file_id)
            
            link_index = next(
                (i for i, f in enumerate(selected_files) if f["id"] == file_id_num),
                None
            )
            
            if link_index is None or link_index >= len(links):
                # Fallback: files may be archived together
                if links:
                    link = links[0]
                else:
                    raise DebridError("Could not find download link for file")
            else:
                link = links[link_index]
            
            # Unrestrict the link
            return self._unrestrict_link(link, filename, size)
            
        except DebridError:
            raise
        except Exception as e:
            raise DebridError(f"Failed to get download link: {e}")

    def _unrestrict_link(self, link: str, filename: str, size: int) -> DebridDirectLink:
        """Convert hoster link to direct download link."""
        self._rate_limit()
        response = self.client.post(
            "/unrestrict/link",
            data={"link": link}
        )
        
        if not response.is_success:
            raise self._handle_error(response.status_code, response.text)
        
        data = response.json()
        
        return DebridDirectLink(
            url=data["download"],
            filename=data["filename"],
            size=data["filesize"]
        )

    def download_file(self, torrent_id: str, file_id: str, destination: str) -> bool:
        """Download file to local destination."""
        try:
            link = self.get_download_link(torrent_id, file_id, "", 0)
            
            log.info(f"Real-Debrid: Starting download to {destination}")
            
            with self.client.stream("GET", link.url, timeout=None) as response:
                response.raise_for_status()
                with open(destination, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            
            log.info(f"Real-Debrid: Download completed: {destination}")
            return True
            
        except Exception as e:
            raise DebridError(f"Download failed: {e}")

    def _extract_hash(self, magnet: str) -> str | None:
        """Extract info hash from magnet link."""
        if "btih:" in magnet:
            start = magnet.find("btih:") + 5
            end = magnet.find("&", start)
            if end == -1:
                end = len(magnet)
            return magnet[start:end].lower()
        return None

    def _find_existing_torrent(self, hash_str: str) -> str | None:
        """Find existing torrent by hash."""
        try:
            self._rate_limit()
            response = self.client.get("/torrents")
            if not response.is_success:
                return None
            
            torrents = response.json()
            target_hash = hash_str.lower()
            
            for t in torrents:
                if t.get("hash", "").lower() == target_hash:
                    return t["id"]
        except Exception:
            pass
        return None
