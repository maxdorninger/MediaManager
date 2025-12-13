"""Debrid Service - unified interface to multiple debrid providers.

Provides a single API for interacting with TorBox, Real-Debrid, or other
debrid services. Handles provider selection, fallback, and cache checking.
"""
import logging
from typing import Protocol

from media_manager.config import AllEncompassingConfig
from media_manager.debrid.realdebrid import RealDebridClient
from media_manager.debrid.schemas import (
    DebridCacheStatus,
    DebridDirectLink,
    DebridError,
    DebridProvider,
    DebridProviderInfo,
    DebridTorrentInfo,
)
from media_manager.debrid.torbox import TorboxClient

log = logging.getLogger(__name__)


class DebridClientProtocol(Protocol):
    """Interface that debrid clients must implement."""

    def get_info(self) -> DebridProviderInfo: ...
    def check_cache(self, hash_str: str) -> DebridCacheStatus: ...
    def add_magnet(self, magnet: str) -> str: ...
    def get_torrent_info(self, torrent_id: str) -> DebridTorrentInfo | None: ...
    def get_download_link(self, torrent_id: str, file_id: str, filename: str, size: int) -> DebridDirectLink: ...
    def download_file(self, torrent_id: str, file_id: str, destination: str) -> str: ...
    def find_torrent_by_hash(self, hash_str: str) -> str | None: ...


class DebridService:
    """Unified debrid interface - tries TorBox first, falls back to Real-Debrid."""

    def __init__(self):
        self.config = AllEncompassingConfig().torrents
        self.torbox_client: TorboxClient | None = None
        self.realdebrid_client: RealDebridClient | None = None
        self.primary_client: DebridClientProtocol | None = None
        self._initialize_clients()

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def get_provider_info(self, provider: DebridProvider | None = None) -> DebridProviderInfo:
        """Get provider metadata for specific or primary provider."""
        client = self._get_client(provider)
        if client:
            return client.get_info()

        return DebridProviderInfo(
            id=DebridProvider.AllDebrid,
            name="None",
            description="No provider configured",
            website="",
            color="gray",
            is_implemented=False,
            supports_cache_check=False,
        )

    def check_cache(self, hash_str: str) -> DebridCacheStatus:
        """Check cache on all providers, return first hit."""
        # Try TorBox first (faster cache checks)
        if self.torbox_client:
            try:
                result = self.torbox_client.check_cache(hash_str)
                if result.is_cached:
                    log.debug(f"Cache hit on TorBox for {hash_str[:8]}...")
                    return result
            except DebridError as e:
                log.warning(f"TorBox cache check failed: {e}")

        # Try Real-Debrid
        if self.realdebrid_client:
            try:
                result = self.realdebrid_client.check_cache(hash_str)
                if result.is_cached:
                    log.debug(f"Cache hit on RealDebrid for {hash_str[:8]}...")
                    return result
            except DebridError as e:
                log.warning(f"RealDebrid cache check failed: {e}")

        if not self.torbox_client and not self.realdebrid_client:
            raise DebridError("No debrid provider configured", code="not_configured")

        return DebridCacheStatus(is_cached=False, provider=None, hash=hash_str)

    def add_magnet(self, magnet: str, provider: DebridProvider | None = None) -> str:
        """Add magnet link to debrid service."""
        client = self._require_client(provider)
        return client.add_magnet(magnet)

    def get_torrent_info(self, torrent_id: str, provider: DebridProvider | None = None) -> DebridTorrentInfo | None:
        """Get torrent details including file list."""
        client = self._require_client(provider)
        return client.get_torrent_info(torrent_id)

    def get_download_link(
        self,
        torrent_id: str,
        file_id: str,
        filename: str,
        size: int,
        provider: DebridProvider | None = None,
    ) -> DebridDirectLink:
        """Get direct download URL for a file."""
        client = self._require_client(provider)
        return client.get_download_link(torrent_id, file_id, filename, size)

    def download_file(
        self,
        torrent_id: str,
        file_id: str,
        destination: str,
        provider: DebridProvider | None = None,
    ) -> str:
        """Download file from debrid to local filesystem."""
        client = self._require_client(provider)
        return client.download_file(torrent_id, file_id, destination)

    def find_torrent_by_hash(self, torrent_hash: str) -> str | None:
        """Find existing torrent ID by hash on primary provider."""
        if not self.primary_client:
            return None
        return self.primary_client.find_torrent_by_hash(torrent_hash)

    # ─────────────────────────────────────────────────────────────────────────
    # Private
    # ─────────────────────────────────────────────────────────────────────────

    def _initialize_clients(self) -> None:
        """Initialize configured debrid clients."""
        if self.config.torbox.enabled and self.config.torbox.api_key:
            self.torbox_client = TorboxClient(api_key=self.config.torbox.api_key)
            log.info("DebridService: TorBox client initialized")

        if self.config.realdebrid.enabled and self.config.realdebrid.api_key:
            self.realdebrid_client = RealDebridClient(api_key=self.config.realdebrid.api_key)
            log.info("DebridService: RealDebrid client initialized")

        # Set primary client (TorBox preferred)
        if self.torbox_client:
            self.primary_client = self.torbox_client
            log.info("DebridService: Primary client set to TorBox")
        elif self.realdebrid_client:
            self.primary_client = self.realdebrid_client
            log.info("DebridService: Primary client set to RealDebrid")
        else:
            log.warning("DebridService: No debrid provider enabled")

    def _get_client(self, provider: DebridProvider | None) -> DebridClientProtocol | None:
        """Get client for provider, or primary if not specified."""
        if provider == DebridProvider.TorBox:
            return self.torbox_client
        if provider == DebridProvider.RealDebrid:
            return self.realdebrid_client
        return self.primary_client

    def _require_client(self, provider: DebridProvider | None = None) -> DebridClientProtocol:
        """Get client, raising error if none available."""
        client = self._get_client(provider)
        if not client:
            raise DebridError("No debrid provider configured", code="not_configured")
        return client


# Singleton instance
debrid_service = DebridService()
