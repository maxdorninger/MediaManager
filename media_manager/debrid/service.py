"""Debrid service - unified interface to debrid providers."""
import logging
from media_manager.config import AllEncompassingConfig
from media_manager.debrid.torbox import TorboxClient
from media_manager.debrid.realdebrid import RealDebridClient
from media_manager.debrid.schemas import DebridProvider, DebridProviderInfo, DebridError, DebridCacheStatus

log = logging.getLogger(__name__)


class DebridService:
    """Tries Torbox first for cache checks, falls back to RealDebrid."""
    
    def __init__(self):
        self.config = AllEncompassingConfig().torrents
        self.torbox_client: TorboxClient | None = None
        self.realdebrid_client: RealDebridClient | None = None
        self.primary_client = None  # The primary client for downloads
        self._initialize_clients()

    def _initialize_clients(self):
        if self.config.torbox.enabled:
            if not self.config.torbox.api_key:
                log.warning("Torbox enabled but no API key provided")
            else:
                self.torbox_client = TorboxClient(api_key=self.config.torbox.api_key)
                log.info("DebridService: Torbox client initialized")
        
        if self.config.realdebrid.enabled:
            if not self.config.realdebrid.api_key:
                log.warning("RealDebrid enabled but no API key provided")
            else:
                self.realdebrid_client = RealDebridClient(api_key=self.config.realdebrid.api_key)
                log.info("DebridService: RealDebrid client initialized")
        
        if self.torbox_client:
            self.primary_client = self.torbox_client
            log.info("DebridService: Primary client set to Torbox")
        elif self.realdebrid_client:
            self.primary_client = self.realdebrid_client
            log.info("DebridService: Primary client set to RealDebrid")
        else:
            log.info("No debrid provider enabled")

    def get_provider_info(self, provider: DebridProvider = None) -> DebridProviderInfo:
        """Get provider info for specific provider, or primary if not specified."""
        if provider == DebridProvider.TorBox and self.torbox_client:
            return self.torbox_client.get_info()
        elif provider == DebridProvider.RealDebrid and self.realdebrid_client:
            return self.realdebrid_client.get_info()
        
        if self.primary_client:
            return self.primary_client.get_info()
        
        return DebridProviderInfo(
            id=DebridProvider.AllDebrid,
            name="None", 
            description="No provider configured", 
            website="", 
            color="gray", 
            is_implemented=False, 
            supports_cache_check=False
        )
    
    def _check_client(self):
        if not self.primary_client:
            raise DebridError("No debrid provider configured", code="not_configured")

    def check_cache(self, hash_str: str) -> DebridCacheStatus:
        """Check cache on Torbox first, then RealDebrid."""
        if self.torbox_client:
            try:
                result = self.torbox_client.check_cache(hash_str)
                if result.is_cached:
                    log.debug(f"Cache hit on Torbox for {hash_str[:8]}...")
                    return result
            except DebridError as e:
                log.warning(f"Torbox cache check failed: {e}")
        
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
        
        return DebridCacheStatus(
            is_cached=False,
            provider=None,
            hash=hash_str
        )

    def add_magnet(self, magnet: str, provider: DebridProvider = None) -> str:
        """Add magnet to specified provider, or primary if not specified."""
        if provider == DebridProvider.TorBox and self.torbox_client:
            return self.torbox_client.add_magnet(magnet)
        elif provider == DebridProvider.RealDebrid and self.realdebrid_client:
            return self.realdebrid_client.add_magnet(magnet)
        
        self._check_client()
        return self.primary_client.add_magnet(magnet)

    def get_torrent_info(self, torrent_id: str, provider: DebridProvider = None):
        """Get torrent info from specified provider, or primary if not specified."""
        if provider == DebridProvider.TorBox and self.torbox_client:
            return self.torbox_client.get_torrent_info(torrent_id)
        elif provider == DebridProvider.RealDebrid and self.realdebrid_client:
            return self.realdebrid_client.get_torrent_info(torrent_id)
        
        self._check_client()
        return self.primary_client.get_torrent_info(torrent_id)

    def get_download_link(self, torrent_id: str, file_id: str, filename: str, size: int, provider: DebridProvider = None):
        """Get download link from specified provider, or primary if not specified."""
        if provider == DebridProvider.TorBox and self.torbox_client:
            return self.torbox_client.get_download_link(torrent_id, file_id, filename, size)
        elif provider == DebridProvider.RealDebrid and self.realdebrid_client:
            return self.realdebrid_client.get_download_link(torrent_id, file_id, filename, size)
        
        self._check_client()
        return self.primary_client.get_download_link(torrent_id, file_id, filename, size)

    def download_file(self, torrent_id: str, file_id: str, destination: str, provider: DebridProvider = None):
        """Download file from specified provider, or primary if not specified."""
        if provider == DebridProvider.TorBox and self.torbox_client:
            return self.torbox_client.download_file(torrent_id, file_id, destination)
        elif provider == DebridProvider.RealDebrid and self.realdebrid_client:
            return self.realdebrid_client.download_file(torrent_id, file_id, destination)
        
        self._check_client()
        return self.primary_client.download_file(torrent_id, file_id, destination)

    def find_torrent_by_hash(self, torrent_hash: str) -> str | None:
        """Find existing torrent ID by hash on the primary provider."""
        self._check_client()
        if hasattr(self.primary_client, '_find_existing_torrent'):
            return self.primary_client._find_existing_torrent(torrent_hash)
        return None


# Singleton instance
debrid_service = DebridService()
