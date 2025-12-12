"""Debrid service download client."""
import logging
import threading
from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.download_clients.abstractDownloadClient import (
    AbstractDownloadClient,
)
from media_manager.torrent.schemas import TorrentStatus, Torrent
from media_manager.torrent.utils import get_torrent_hash
from media_manager.debrid.service import DebridService
from media_manager.debrid.schemas import DebridError, DebridProviderInfo

log = logging.getLogger(__name__)

VIDEO_EXTENSIONS = frozenset([".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv"])
ARCHIVE_EXTENSIONS = frozenset([".rar", ".zip", ".7z", ".tar", ".gz", ".tar.gz", ".tgz"])


class DebridDownloadClient(AbstractDownloadClient):
    """Downloads cached torrents instantly; uncached ones go to debrid first."""
    name = "debrid"

    def __init__(self):
        self.config = AllEncompassingConfig().torrents
        self.service = DebridService()
        self.provider_info: DebridProviderInfo = self.service.get_provider_info()
        log.info(f"Debrid download client initialized with {self.provider_info.name}")

    def download_torrent(self, indexer_result: IndexerQueryResult) -> Torrent:
        log.info(f"Attempting to download torrent: {indexer_result.title}")
        torrent_hash = get_torrent_hash(torrent=indexer_result)

        try:
            cache_status = self.service.check_cache(torrent_hash)
            is_cached = cache_status.is_cached
            cached_provider = cache_status.provider
            log.info(f"Debrid: Cache status for {indexer_result.title}: {'CACHED on ' + str(cached_provider) if is_cached else 'NOT CACHED'}")
            
            # Add magnet to the provider that has the cache (or primary if not cached)
            torrent_id = self.service.add_magnet(str(indexer_result.download_url), provider=cached_provider)
            log.info(f"Debrid: Added torrent {indexer_result.title}, ID: {torrent_id}")
            
            torrent = Torrent(
                status=TorrentStatus.finished if is_cached else TorrentStatus.downloading,
                title=indexer_result.title,
                quality=indexer_result.quality,
                imported=False,
                hash=torrent_hash,
            )
            
            if is_cached:
                # Download in background thread to avoid blocking HTTP request
                log.info(f"Debrid: Starting background download for cached torrent: {indexer_result.title}")
                download_thread = threading.Thread(
                    target=self._download_files,
                    args=(torrent, torrent_id, cached_provider),
                    daemon=True
                )
                download_thread.start()
            
            return torrent

        except DebridError as e:
            log.error(f"Debrid: Failed to add torrent: {e}")
            raise RuntimeError(f"Debrid error: {e}")

    def remove_torrent(self, torrent: Torrent, delete_data: bool = False) -> None:
        log.info(f"Removing torrent: {torrent.title}")
        # Note: delete not implemented via DebridService yet
        log.warning("Debrid: remove_torrent not fully implemented")

    def get_torrent_status(self, torrent: Torrent) -> TorrentStatus:
        try:
            torrent_id = self._get_id_by_hash(torrent.hash)
            if not torrent_id:
                return TorrentStatus.unknown
            
            info = self.service.get_torrent_info(torrent_id)
            # Debrid torrents are either ready or not
            return TorrentStatus.finished if info else TorrentStatus.downloading
            
        except Exception as e:
            log.error(f"Debrid: Error getting torrent status: {e}")
            return TorrentStatus.unknown

    def pause_torrent(self, torrent: Torrent) -> None:
        log.debug("Debrid: pause_torrent not supported")

    def resume_torrent(self, torrent: Torrent) -> None:
        log.debug("Debrid: resume_torrent not supported")

    def download_files_locally(self, torrent: Torrent) -> bool:
        """Called by import scheduler for torrents that weren't cached initially."""
        torrent_id = self._get_id_by_hash(torrent.hash)
        if not torrent_id:
            log.error(f"Debrid: Could not find torrent ID for hash {torrent.hash}")
            return False
        
        return self._download_files(torrent, torrent_id, provider=None)

    def _download_files(self, torrent: Torrent, torrent_id: str, provider=None) -> bool:
        from media_manager.debrid.schemas import DebridProvider
        
        try:
            torrent_info = self.service.get_torrent_info(torrent_id, provider=provider)
            if not torrent_info or not torrent_info.files:
                log.warning(f"Debrid: No files found for torrent {torrent.title}")
                return False
            
            target_file = self._select_target_file(torrent_info.files)
            log.info(f"Debrid: Selected {target_file.name} ({target_file.size:,} bytes)")
            
            config = AllEncompassingConfig()
            destination = config.misc.torrent_directory / torrent.title / target_file.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            log.info(f"Debrid: Downloading to {destination}")
            self.service.download_file(
                torrent_id=torrent_id,
                file_id=target_file.id,
                destination=str(destination),
                provider=provider
            )
            
            log.info(f"Debrid: Download complete: {target_file.name}")
            
            # Check if this provider returns archives (get provider info)
            provider_info = self.service.get_provider_info(provider)
            if provider_info.returns_archives and self._is_archive(destination):
                self._extract_archive(destination)
            
            # Trigger immediate import (don't wait for scheduler)
            self._trigger_import(torrent)
            
            return True
            
        except DebridError as e:
            log.error(f"Debrid: Download error: {e}")
            return False
        except Exception as e:
            log.error(f"Debrid: Unexpected error: {e}")
            return False

    def _trigger_import(self, torrent: Torrent) -> None:
        """Trigger immediate import after debrid download completes."""
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
                torrent_repo = TorrentRepository(db=db)
                torrent_service = TorrentService(torrent_repository=torrent_repo)
                
                # Get the saved torrent from DB by hash
                db_torrent = None
                for t in torrent_repo.get_all_torrents():
                    if t.hash and t.hash.lower() == torrent.hash.lower():
                        db_torrent = t
                        break
                
                if not db_torrent:
                    log.warning(f"Debrid: Could not find torrent in DB for import: {torrent.title}")
                    return
                
                # Try movie import first
                movie = torrent_service.get_movie_of_torrent(torrent=db_torrent)
                if movie:
                    movie_repo = MovieRepository(db=db)
                    indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
                    movie_service = MovieService(
                        movie_repository=movie_repo,
                        torrent_service=torrent_service,
                        indexer_service=indexer_service,
                    )
                    log.info(f"Debrid: Importing movie torrent immediately: {db_torrent.title}")
                    movie_service.import_torrent_files(torrent=db_torrent, movie=movie)
                    db.commit()
                    return
                
                # Try TV show import
                show = torrent_service.get_show_of_torrent(torrent=db_torrent)
                if show:
                    tv_repo = TvRepository(db=db)
                    indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
                    tv_service = TvService(
                        tv_repository=tv_repo,
                        torrent_service=torrent_service,
                        indexer_service=indexer_service,
                    )
                    log.info(f"Debrid: Importing TV torrent immediately: {db_torrent.title}")
                    tv_service.import_torrent_files(torrent=db_torrent, show=show)
                    db.commit()
                    return
                
                log.warning(f"Debrid: Torrent not linked to movie or show: {db_torrent.title}")
                
        except Exception as e:
            log.error(f"Debrid: Failed to trigger immediate import: {e}")

    def _is_archive(self, file_path) -> bool:
        """Check if file is an archive that needs extraction."""
        name = str(file_path).lower()
        return any(name.endswith(ext) for ext in ARCHIVE_EXTENSIONS)

    def _extract_archive(self, archive_path) -> bool:
        """Extract archive and delete the original archive file."""
        import subprocess
        from pathlib import Path
        
        archive_path = Path(archive_path)
        extract_dir = archive_path.parent
        
        log.info(f"Debrid: Extracting archive {archive_path.name}")
        
        try:
            # Use unar which handles rar, zip, 7z, etc. (installed in Docker image)
            result = subprocess.run(
                ['unar', '-f', '-o', str(extract_dir), str(archive_path)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                log.info(f"Debrid: Extraction successful, deleting archive")
                archive_path.unlink()
                
                # Also delete any .r00, .r01, etc. files (multi-part rar)
                for part_file in extract_dir.glob('*.r[0-9][0-9]'):
                    log.info(f"Debrid: Deleting archive part: {part_file.name}")
                    part_file.unlink()
                
                return True
            else:
                log.error(f"Debrid: Extraction failed: {result.stderr}")
                return False
                
        except FileNotFoundError as e:
            log.error(f"Debrid: unar not found (install unar package): {e}")
            return False
        except Exception as e:
            log.error(f"Debrid: Extraction error: {e}")
            return False

    def _select_target_file(self, files: list) -> object:
        video_files = [
            f for f in files 
            if any(f.name.lower().endswith(ext) for ext in VIDEO_EXTENSIONS)
        ]
        
        if video_files:
            return max(video_files, key=lambda f: f.size)
        
        log.warning("Debrid: No video files found, using largest file")
        return max(files, key=lambda f: f.size)

    def _get_id_by_hash(self, torrent_hash: str) -> str | None:
        try:
            return self.service.find_torrent_by_hash(torrent_hash)
        except Exception:
            return None
