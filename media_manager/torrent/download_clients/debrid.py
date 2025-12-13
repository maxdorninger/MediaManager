"""Debrid service download client.

Unlike traditional torrent clients that download to a local directory,
debrid services store files remotely. Files are only "finished" once
downloaded locally via resume_torrent() or the import scheduler.
"""
import logging
import threading
from pathlib import Path
from typing import Optional

from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstractDownloadClient import AbstractDownloadClient
from media_manager.torrent.schemas import TorrentStatus, Torrent
from media_manager.torrent.utils import get_torrent_hash
from media_manager.debrid.service import DebridService
from media_manager.debrid.schemas import DebridError, DebridProvider, DebridProviderInfo

log = logging.getLogger(__name__)

VIDEO_EXTENSIONS = frozenset([".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv"])


class DebridDownloadClient(AbstractDownloadClient):
    """Debrid download client - files stay remote until explicitly downloaded."""
    
    name = "debrid"
    _pending_downloads: dict = {}

    def __init__(self):
        self.config = AllEncompassingConfig()
        self.service = DebridService()
        self.provider_info: DebridProviderInfo = self.service.get_provider_info()
        log.info(f"Debrid client initialized: {self.provider_info.name}")

    # ─────────────────────────────────────────────────────────────────────────
    # Public API (AbstractDownloadClient interface)
    # ─────────────────────────────────────────────────────────────────────────

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        """Add torrent to debrid service. If cached, queue for local download."""
        torrent_hash = get_torrent_hash(torrent=indexer_result)
        
        try:
            cache_status = self.service.check_cache(torrent_hash)
            log.info(f"Cache: {indexer_result.title} -> {'HIT' if cache_status.is_cached else 'MISS'}")
            
            torrent_id = self.service.add_magnet(
                str(indexer_result.download_url), 
                provider=cache_status.provider
            )
            
            torrent = Torrent(
                status=TorrentStatus.downloading,
                title=indexer_result.title,
                quality=indexer_result.quality,
                imported=False,
                hash=torrent_hash,
            )
            
            if cache_status.is_cached:
                DebridDownloadClient._pending_downloads[torrent_hash] = {
                    "torrent": torrent,
                    "torrent_id": torrent_id,
                    "provider": cache_status.provider,
                }
            
            return torrent

        except DebridError as e:
            log.error(f"Failed to add torrent: {e}")
            raise RuntimeError(f"Debrid error: {e}")

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        """Check if files exist locally in staging directory."""
        torrent_hash = torrent.hash.lower() if torrent.hash else None
        
        if torrent_hash and torrent_hash in DebridDownloadClient._pending_downloads:
            return TorrentStatus.downloading
        
        if self._files_exist_locally(torrent):
            return TorrentStatus.finished
        
        if not self._get_remote_id(torrent.hash):
            return TorrentStatus.unknown
        
        return TorrentStatus.downloading

    def resume_torrent(self, torrent: Torrent) -> None:
        """Start background download after media is linked in DB."""
        torrent_hash = torrent.hash.lower() if torrent.hash else None
        
        if not torrent_hash or torrent_hash not in DebridDownloadClient._pending_downloads:
            return
        
        pending = DebridDownloadClient._pending_downloads.pop(torrent_hash)
        log.info(f"Starting download: {torrent.title}")
        
        threading.Thread(
            target=self._execute_download,
            args=(pending["torrent"], pending["torrent_id"], pending["provider"]),
            daemon=True
        ).start()

    def download_files_locally(self, torrent: Torrent) -> bool:
        """Manual download trigger for uncached torrents."""
        torrent_id = self._get_remote_id(torrent.hash)
        if not torrent_id:
            log.error(f"No remote torrent found: {torrent.hash}")
            return False
        return self._execute_download(torrent, torrent_id, provider=None)

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        log.warning("remove_torrent: not implemented for debrid")

    def pause_torrent(self, torrent: Torrent) -> None:
        pass

    # ─────────────────────────────────────────────────────────────────────────
    # Private: Download execution
    # ─────────────────────────────────────────────────────────────────────────

    def _execute_download(self, torrent: Torrent, torrent_id: str, provider: Optional[DebridProvider]) -> bool:
        """Download file from debrid to local filesystem, then update DB."""
        try:
            torrent_info = self.service.get_torrent_info(torrent_id, provider=provider)
            if not torrent_info or not torrent_info.files:
                log.warning(f"No files found: {torrent.title}")
                return False
            
            target_file = self._select_video_file(torrent_info.files)
            filename = target_file.name.lstrip("/").rsplit("/", 1)[-1]
            destination = self._resolve_destination(torrent, filename)
            
            destination.parent.mkdir(parents=True, exist_ok=True)
            log.info(f"Downloading: {filename} -> {destination}")
            
            self.service.download_file(
                torrent_id=torrent_id,
                file_id=target_file.id,
                destination=str(destination),
                provider=provider
            )
            
            self._finalize_download(torrent)
            return True
            
        except Exception as e:
            log.error(f"Download failed: {e}")
            return False

    def _resolve_destination(self, torrent: Torrent, filename: str) -> Path:
        """Always use staging directory - import scheduler handles final location."""
        return self.config.misc.torrent_directory / torrent.title / filename

    def _finalize_download(self, torrent: Torrent) -> None:
        """Mark as finished and trigger immediate import - no waiting for scheduler."""
        log.info(f"Finalizing download: {torrent.title}")
        
        try:
            from media_manager.database import get_session
            from media_manager.torrent.repository import TorrentRepository
            from media_manager.torrent.service import TorrentService
            from media_manager.movies.repository import MovieRepository
            from media_manager.movies.service import MovieService
            from media_manager.tv.repository import TvRepository
            from media_manager.tv.service import TvService
            from media_manager.indexer.repository import IndexerRepository
            from media_manager.indexer.service import IndexerService
            
            with next(get_session()) as db:
                db_torrent = self._find_db_torrent(db, torrent.hash)
                if not db_torrent:
                    log.warning(f"Could not find torrent in DB: {torrent.hash}")
                    return
                
                db_torrent.status = TorrentStatus.finished
                
                torrent_repo = TorrentRepository(db=db)
                torrent_service = TorrentService(torrent_repository=torrent_repo)
                indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
                
                movie = torrent_service.get_movie_of_torrent(torrent=db_torrent)
                if movie:
                    log.info(f"Importing movie files: {movie.name}")
                    movie_service = MovieService(
                        movie_repository=MovieRepository(db=db),
                        torrent_service=torrent_service,
                        indexer_service=indexer_service,
                    )
                    movie_service.import_torrent_files(torrent=db_torrent, movie=movie)
                    log.info(f"Imported movie: {movie.name}")
                else:
                    show = torrent_service.get_show_of_torrent(torrent=db_torrent)
                    if show:
                        log.info(f"Importing TV files: {show.name}")
                        tv_service = TvService(
                            tv_repository=TvRepository(db=db),
                            torrent_service=torrent_service,
                            indexer_service=indexer_service,
                        )
                        tv_service.import_torrent_files(torrent=db_torrent, show=show)
                        log.info(f"Imported TV show: {show.name}")
                    else:
                        log.warning(f"Torrent not linked to any movie or show: {torrent.title}")
                
                db.commit()
                log.info(f"Finalize complete: {torrent.title}")
                
        except Exception as e:
            log.error(f"Error in _finalize_download: {e}", exc_info=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Private: Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _files_exist_locally(self, torrent: Torrent) -> bool:
        torrent_dir = self.config.misc.torrent_directory / torrent.title
        return torrent_dir.exists() and any(torrent_dir.iterdir())

    def _get_remote_id(self, torrent_hash: str) -> Optional[str]:
        try:
            return self.service.find_torrent_by_hash(torrent_hash)
        except Exception:
            return None

    def _find_db_torrent(self, db, torrent_hash: str):
        from media_manager.torrent.repository import TorrentRepository
        for t in TorrentRepository(db=db).get_all_torrents():
            if t.hash and t.hash.lower() == torrent_hash.lower():
                return t
        return None

    def _select_video_file(self, files: list):
        video_files = [f for f in files if any(f.name.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)]
        return max(video_files or files, key=lambda f: f.size)
