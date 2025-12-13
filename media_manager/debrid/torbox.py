"""TorBox API Client.

TorBox is a premium debrid service providing cached torrent downloads.
API Docs: https://api.torbox.app/docs and https://documenter.getpostman.com/view/29572726/2s9YXo1zX4
"""
import logging
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

BASE_URL = "https://api.torbox.app/v1/api"


class TorboxClient:
    """Client for TorBox debrid API."""

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
            id=DebridProvider.TorBox,
            name="TorBox",
            description="Premium debrid service with instant cached downloads",
            website="https://torbox.app",
            color="emerald",
            is_implemented=True,
            supports_cache_check=True,
            rate_limit_seconds=0.25,
        )

    def check_cache(self, hash_str: str) -> DebridCacheStatus:
        """Check if torrent is cached on TorBox servers."""
        data = self._request("GET", "/torrents/checkcached", params={
            "hash": hash_str,
            "format": "list",
            "list_files": "true",
        })

        cached_items = data.get("data", [])
        if cached_items:
            item = cached_items[0]
            return DebridCacheStatus(
                is_cached=True,
                provider=DebridProvider.TorBox,
                name=item.get("name"),
                size=item.get("size"),
                hash=item.get("hash"),
            )

        return DebridCacheStatus(
            is_cached=False,
            name=None,
            size=None,
            hash=hash_str,
        )

    def add_magnet(self, magnet: str) -> str:
        """Add magnet link and return torrent ID."""
        data = self._request("POST", "/torrents/createtorrent", data={
            "magnet": magnet,
            "seed": "3",
            "add_only_if_cached": "false",
        })
        return str(data["data"]["torrent_id"])

    def get_torrent_info(self, torrent_id: str) -> DebridTorrentInfo | None:
        """Get torrent details including file list."""
        data = self._request("GET", "/torrents/mylist", params={
            "id": torrent_id,
            "bypass_cache": "true",
        })

        torrent = data.get("data")
        if not torrent:
            return None

        files = [
            DebridFile(
                id=str(f["id"]),
                name=f["name"],
                short_name=f["short_name"],
                size=f["size"],
            )
            for f in torrent.get("files") or []
        ]

        return DebridTorrentInfo(
            id=str(torrent["id"]),
            name=torrent["name"],
            size=torrent["size"],
            hash=torrent["hash"],
            files=files,
        )

    def get_download_link(self, torrent_id: str, file_id: str, filename: str, size: int) -> DebridDirectLink:
        """Get direct download URL for a file."""
        data = self._request("GET", "/torrents/requestdl", params={
            "token": self.api_key,
            "torrent_id": torrent_id,
            "file_id": file_id,
        })

        return DebridDirectLink(
            url=data["data"],
            filename=filename,
            size=size,
        )

    def download_file(self, torrent_id: str, file_id: str, destination: str) -> str:
        """Stream file to local path. Returns the destination path."""
        link = self.get_download_link(torrent_id, file_id, "", 0)

        log.info(f"TorBox: Downloading to {destination}")
        with self.client.stream("GET", link.url, timeout=None) as response:
            response.raise_for_status()
            with open(destination, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        log.info(f"TorBox: Download complete: {destination}")
        return destination

    def delete_torrent(self, torrent_id: str) -> None:
        """Delete torrent from TorBox."""
        self._request("POST", "/torrents/controltorrent", json={
            "torrent_id": torrent_id,
            "operation": "delete",
        })

    def find_torrent_by_hash(self, hash_str: str) -> str | None:
        """Find existing torrent by hash, returns torrent ID or None."""
        try:
            data = self._request("GET", "/torrents/mylist", params={
                "bypass_cache": "true",
            })
            for torrent in data.get("data", []):
                if torrent.get("hash", "").lower() == hash_str.lower():
                    return str(torrent["id"])
        except DebridError:
            pass
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Private
    # ─────────────────────────────────────────────────────────────────────────

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Execute API request with error handling."""
        try:
            response = self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise DebridError(data.get("detail", "Unknown TorBox API error"))

            return data

        except httpx.HTTPError as e:
            raise DebridError(f"TorBox network error: {e}")
