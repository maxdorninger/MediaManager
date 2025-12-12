import logging
import httpx
from typing import Optional
from media_manager.debrid.schemas import (
    DebridCacheStatus,
    DebridTorrentInfo,
    DebridFile,
    DebridDirectLink,
    DebridError,
    DebridProvider,
    DebridProviderInfo
)

log = logging.getLogger(__name__)

class TorboxClient:
    BASE_URL = "https://api.torbox.app/v1/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0
        )

    def get_info(self) -> DebridProviderInfo:
        return DebridProviderInfo(
            id=DebridProvider.TorBox,
            name="TorBox",
            description="Premium debrid service with instant cached downloads",
            website="https://torbox.app",
            color="emerald",
            is_implemented=True,
            supports_cache_check=True,
            returns_archives=False,
            rate_limit_seconds=0.0,
        )

    def check_cache(self, hash_str: str) -> DebridCacheStatus:
        try:
            response = self.client.get(
                "/torrents/checkcached",
                params={"hash": hash_str, "format": "list", "list_files": "true"}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success"):
                raise DebridError(data.get("detail", "Unknown API error"))

            cached_items = data.get("data", [])
            if cached_items:
                cached = cached_items[0]
                return DebridCacheStatus(
                    is_cached=True,
                    provider=DebridProvider.TorBox,
                    name=cached.get("name"),
                    size=cached.get("size"),
                    hash=cached.get("hash")
                )
            else:
                return DebridCacheStatus(
                    is_cached=False,
                    name=None,
                    size=None,
                    hash=hash_str
                )
        except httpx.HTTPError as e:
            raise DebridError(f"Network error: {str(e)}")

    def add_magnet(self, magnet: str) -> str:
        try:
            response = self.client.post(
                "/torrents/createtorrent",
                data={
                    "magnet": magnet,
                    "seed": "3",
                    "add_only_if_cached": "false"
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise DebridError(data.get("detail", "Unknown API error"))

            return str(data["data"]["torrent_id"])
        except httpx.HTTPError as e:
            raise DebridError(f"Network error: {str(e)}")

    def get_torrent_info(self, torrent_id: str) -> DebridTorrentInfo | None:
        try:
            response = self.client.get(
                "/torrents/mylist",
                params={"id": torrent_id, "bypass_cache": "true"}
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise DebridError(data.get("detail", "Unknown API error"))

            torrent_data = data.get("data")
            if torrent_data is None:
                return None  # Torrent not found
            
            files = [
                DebridFile(
                    id=str(f["id"]),
                    name=f["name"],
                    short_name=f["short_name"],
                    size=f["size"]
                )
                for f in torrent_data.get("files") or []
            ]

            return DebridTorrentInfo(
                id=str(torrent_data["id"]),
                name=torrent_data["name"],
                size=torrent_data["size"],
                hash=torrent_data["hash"],
                files=files
            )
        except httpx.HTTPError as e:
            raise DebridError(f"Network error: {str(e)}")

    def get_download_link(self, torrent_id: str, file_id: str, filename: str, size: int) -> DebridDirectLink:
        try:
            response = self.client.get(
                "/torrents/requestdl",
                params={
                    "token": self.api_key, 
                    "torrent_id": torrent_id, 
                    "file_id": file_id
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise DebridError(data.get("detail", "Unknown API error"))

            return DebridDirectLink(
                url=data["data"],
                filename=filename,
                size=size
            )
        except httpx.HTTPError as e:
            raise DebridError(f"Network error: {str(e)}")
            
    def delete_torrent(self, torrent_id: str):
        try:
             response = self.client.post(
                "/torrents/controltorrent",
                json={
                    "torrent_id": torrent_id,
                    "operation": "delete"
                }
            )
             response.raise_for_status()
        except httpx.HTTPError as e:
            raise DebridError(f"Network error: {str(e)}")

    def download_file(self, torrent_id: str, file_id: str, destination: str):
        try:
            link_info = self.get_download_link(torrent_id, file_id, "dummy", 0)
            download_url = link_info.url

            log.info(f"Starting download from {download_url} to {destination}")

            with self.client.stream("GET", download_url, timeout=None) as response:
                response.raise_for_status()
                with open(destination, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            
            log.info(f"Download completed: {destination}")
            return True

        except Exception as e:
            raise DebridError(f"Download failed: {str(e)}")

    def _find_existing_torrent(self, hash_str: str) -> str | None:
        try:
            response = self.client.get(
                "/torrents/mylist",
                params={"bypass_cache": "true"}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                for t in data.get("data", []):
                    if t.get("hash", "").lower() == hash_str.lower():
                        return str(t.get("id"))
        except Exception:
            pass
        return None
