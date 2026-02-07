import mimetypes
import shutil
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from media_manager.config import MediaManagerConfig
from media_manager.database import SessionLocal, get_session
from media_manager.exceptions import NotFoundError
from media_manager.indexer.repository import IndexerRepository
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.indexer.service import IndexerService
from media_manager.metadataProvider.abstract_music_metadata_provider import (
    AbstractMusicMetadataProvider,
)
from media_manager.metadataProvider.musicbrainz import MusicBrainzMetadataProvider
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.music import log
from media_manager.music.repository import MusicRepository
from media_manager.music.schemas import (
    AlbumFile,
    AlbumId,
    AlbumRequest,
    AlbumRequestId,
    Artist,
    ArtistId,
    PublicAlbumFile,
    PublicArtist,
    RichAlbumRequest,
    RichArtistTorrent,
)
from media_manager.notification.repository import NotificationRepository
from media_manager.notification.service import NotificationService
from media_manager.torrent.repository import TorrentRepository
from media_manager.torrent.schemas import (
    Quality,
    QualityStrings,
    Torrent,
    TorrentStatus,
)
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import (
    import_file,
    list_files_recursively,
    remove_special_characters,
)

AUDIO_EXTENSIONS = {".flac", ".mp3", ".ogg", ".m4a", ".opus", ".wav", ".aac", ".wma", ".alac"}


class MusicService:
    def __init__(
        self,
        music_repository: MusicRepository,
        torrent_service: TorrentService,
        indexer_service: IndexerService,
        notification_service: NotificationService,
    ) -> None:
        self.music_repository = music_repository
        self.torrent_service = torrent_service
        self.indexer_service = indexer_service
        self.notification_service = notification_service

    def add_artist(
        self,
        external_id: str,
        metadata_provider: AbstractMusicMetadataProvider,
    ) -> Artist:
        artist_with_metadata = metadata_provider.get_artist_metadata(
            artist_id=external_id
        )
        if not artist_with_metadata:
            raise NotFoundError

        saved_artist = self.music_repository.save_artist(artist=artist_with_metadata)
        metadata_provider.download_artist_cover_image(artist=saved_artist)
        return saved_artist

    def add_album_request(self, album_request: AlbumRequest) -> AlbumRequest:
        return self.music_repository.add_album_request(album_request=album_request)

    def get_album_request_by_id(
        self, album_request_id: AlbumRequestId
    ) -> AlbumRequest:
        return self.music_repository.get_album_request(
            album_request_id=album_request_id
        )

    def update_album_request(self, album_request: AlbumRequest) -> AlbumRequest:
        self.music_repository.delete_album_request(
            album_request_id=album_request.id
        )
        return self.music_repository.add_album_request(album_request=album_request)

    def delete_album_request(self, album_request_id: AlbumRequestId) -> None:
        self.music_repository.delete_album_request(
            album_request_id=album_request_id
        )

    def delete_artist(
        self,
        artist: Artist,
        delete_files_on_disk: bool = False,
        delete_torrents: bool = False,
    ) -> None:
        if delete_files_on_disk or delete_torrents:
            if delete_files_on_disk:
                artist_dir = self.get_artist_root_path(artist=artist)
                if artist_dir.exists() and artist_dir.is_dir():
                    try:
                        shutil.rmtree(artist_dir)
                        log.info(f"Deleted artist directory: {artist_dir}")
                    except OSError:
                        log.exception(f"Deleting artist directory: {artist_dir}")

            if delete_torrents:
                artist_torrents = self.music_repository.get_torrents_by_artist_id(
                    artist_id=artist.id
                )
                for album_torrent in artist_torrents:
                    torrent = self.torrent_service.get_torrent_by_id(
                        torrent_id=album_torrent.torrent_id
                    )
                    try:
                        self.torrent_service.cancel_download(
                            torrent=torrent, delete_files=True
                        )
                        log.info(f"Deleted torrent: {torrent.title}")
                    except Exception:
                        log.warning(
                            f"Failed to delete torrent {torrent.hash}",
                            exc_info=True,
                        )

        self.music_repository.delete_artist(artist_id=artist.id)

    def get_public_album_files(
        self, album_id: AlbumId
    ) -> list[PublicAlbumFile]:
        album_files = self.music_repository.get_album_files_by_album_id(
            album_id=album_id
        )
        public_album_files = [PublicAlbumFile.model_validate(x) for x in album_files]
        result = []
        for album_file in public_album_files:
            album_file.downloaded = self.album_file_exists_on_disk(
                album_file=album_file
            )
            result.append(album_file)
        return result

    def album_file_exists_on_disk(self, album_file: AlbumFile) -> bool:
        if album_file.torrent_id is None:
            return True
        torrent_file = self.torrent_service.get_torrent_by_id(
            torrent_id=album_file.torrent_id
        )
        return torrent_file.imported

    def get_all_artists(self) -> list[Artist]:
        return self.music_repository.get_artists()

    def search_for_artist(
        self, query: str, metadata_provider: AbstractMusicMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        results = metadata_provider.search_artist(query)
        for result in results:
            try:
                artist = self.music_repository.get_artist_by_external_id(
                    external_id=str(result.external_id),
                    metadata_provider=metadata_provider.name,
                )
                result.added = True
                result.id = artist.id
            except NotFoundError:
                pass
            except Exception:
                log.error(
                    f"Unable to find internal artist ID for {result.external_id} on {metadata_provider.name}"
                )
        return results

    def get_public_artist_by_id(self, artist: Artist) -> PublicArtist:
        torrents = self.get_torrents_for_artist(artist=artist).torrents
        public_artist = PublicArtist.model_validate(artist)
        for album in public_artist.albums:
            album_files = self.music_repository.get_album_files_by_album_id(
                album_id=album.id
            )
            album.downloaded = len(album_files) > 0
        return public_artist

    def get_artist_by_id(self, artist_id: ArtistId) -> Artist:
        return self.music_repository.get_artist_by_id(artist_id=artist_id)

    def get_artist_by_external_id(
        self, external_id: str, metadata_provider: str
    ) -> Artist | None:
        return self.music_repository.get_artist_by_external_id(
            external_id=external_id, metadata_provider=metadata_provider
        )

    def get_all_album_requests(self) -> list[RichAlbumRequest]:
        return self.music_repository.get_album_requests()

    def set_artist_library(self, artist: Artist, library: str) -> None:
        self.music_repository.set_artist_library(
            artist_id=artist.id, library=library
        )

    def get_torrents_for_artist(self, artist: Artist) -> RichArtistTorrent:
        artist_torrents = self.music_repository.get_torrents_by_artist_id(
            artist_id=artist.id
        )
        return RichArtistTorrent(
            artist_id=artist.id,
            name=artist.name,
            metadata_provider=artist.metadata_provider,
            torrents=artist_torrents,
        )

    def get_all_artists_with_torrents(self) -> list[RichArtistTorrent]:
        artists = self.music_repository.get_all_artists_with_torrents()
        return [self.get_torrents_for_artist(artist=artist) for artist in artists]

    def get_all_available_torrents_for_album(
        self,
        artist: Artist,
        album_name: str,
        search_query_override: str | None = None,
    ) -> list[IndexerQueryResult]:
        return self.indexer_service.search_music(
            artist=artist,
            album_name=album_name,
            search_query_override=search_query_override,
        )

    def download_torrent(
        self,
        public_indexer_result_id: IndexerQueryResultId,
        artist: Artist,
        album_id: AlbumId,
        override_file_path_suffix: str = "",
    ) -> Torrent:
        indexer_result = self.indexer_service.get_result(
            result_id=public_indexer_result_id
        )
        album_torrent = self.torrent_service.download(indexer_result=indexer_result)
        self.torrent_service.pause_download(torrent=album_torrent)
        album_file = AlbumFile(
            album_id=album_id,
            quality=indexer_result.quality,
            torrent_id=album_torrent.id,
            file_path_suffix=override_file_path_suffix,
        )
        try:
            self.music_repository.add_album_file(album_file=album_file)
        except IntegrityError:
            log.warning(
                f"Album file for artist {artist.name} and torrent {album_torrent.title} already exists"
            )
            self.torrent_service.cancel_download(
                torrent=album_torrent, delete_files=True
            )
            raise
        else:
            log.info(
                f"Added album file for artist {artist.name} and torrent {album_torrent.title}"
            )
            self.torrent_service.resume_download(torrent=album_torrent)
        return album_torrent

    def download_approved_album_request(
        self, album_request: AlbumRequest, artist: Artist, album_name: str
    ) -> bool:
        if not album_request.authorized:
            msg = "Album request is not authorized"
            raise ValueError(msg)

        log.info(f"Downloading approved album request {album_request.id}")

        torrents = self.get_all_available_torrents_for_album(
            artist=artist, album_name=album_name
        )
        available_torrents: list[IndexerQueryResult] = []

        for torrent in torrents:
            if torrent.seeders < 3:
                log.debug(
                    f"Skipping torrent {torrent.title} for album request {album_request.id}, too few seeders"
                )
            else:
                available_torrents.append(torrent)

        if len(available_torrents) == 0:
            log.warning(
                f"No torrents found for album request {album_request.id}"
            )
            return False

        available_torrents.sort()

        torrent = self.torrent_service.download(indexer_result=available_torrents[0])
        album_file = AlbumFile(
            album_id=album_request.album_id,
            quality=torrent.quality,
            torrent_id=torrent.id,
            file_path_suffix=QualityStrings[torrent.quality.name].value.upper(),
        )
        try:
            self.music_repository.add_album_file(album_file=album_file)
        except IntegrityError:
            log.warning(
                f"Album file for torrent {torrent.title} already exists"
            )
        self.delete_album_request(album_request.id)
        return True

    def get_artist_root_path(self, artist: Artist) -> Path:
        misc_config = MediaManagerConfig().misc
        artist_dir_name = remove_special_characters(artist.name)
        artist_file_path = misc_config.music_directory / artist_dir_name

        if artist.library != "Default":
            for library in misc_config.music_libraries:
                if library.name == artist.library:
                    log.debug(
                        f"Using library {library.name} for artist {artist.name}"
                    )
                    return Path(library.path) / artist_dir_name
            log.warning(
                f"Library {artist.library} not found in config, using default library"
            )
        return artist_file_path

    def import_music_files(self, torrent: Torrent, artist: Artist) -> None:
        from media_manager.torrent.utils import get_torrent_filepath

        torrent_path = get_torrent_filepath(torrent=torrent)
        all_files = list_files_recursively(path=torrent_path)

        audio_files = [
            f
            for f in all_files
            if f.suffix.lower() in AUDIO_EXTENSIONS
            or (mimetypes.guess_type(str(f))[0] or "").startswith("audio")
        ]

        if not audio_files:
            log.warning(
                f"No audio files found in torrent {torrent.title} for artist {artist.name}"
            )
            return

        log.info(
            f"Found {len(audio_files)} audio files for import from torrent {torrent.title}"
        )

        artist_root = self.get_artist_root_path(artist=artist)
        album_dir = artist_root / remove_special_characters(torrent.title)

        try:
            album_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            log.exception(f"Failed to create directory {album_dir}")
            return

        success = True
        for audio_file in audio_files:
            target_file = album_dir / audio_file.name
            try:
                import_file(target_file=target_file, source_file=audio_file)
            except Exception:
                log.exception(f"Failed to import audio file {audio_file}")
                success = False

        if success:
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)

            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Music Downloaded",
                    message=f"Music for {artist.name} has been successfully downloaded and imported.",
                )
        else:
            log.error(
                f"Failed to import some files for torrent {torrent.title}."
            )
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Import Failed",
                    message=f"Failed to import some music files for {artist.name}. Please check logs.",
                )

    def update_artist_metadata(
        self,
        db_artist: Artist,
        metadata_provider: AbstractMusicMetadataProvider,
    ) -> Artist | None:
        log.debug(f"Found artist: {db_artist.name} for metadata update.")

        fresh_artist_data = metadata_provider.get_artist_metadata(
            artist_id=db_artist.external_id
        )
        if not fresh_artist_data:
            log.warning(
                f"Could not fetch fresh metadata for artist: {db_artist.name} (ID: {db_artist.external_id})"
            )
            return None

        self.music_repository.update_artist_attributes(
            artist_id=db_artist.id,
            name=fresh_artist_data.name,
            overview=fresh_artist_data.overview,
            country=fresh_artist_data.country,
            disambiguation=fresh_artist_data.disambiguation,
        )

        updated_artist = self.music_repository.get_artist_by_id(
            artist_id=db_artist.id
        )
        log.info(f"Successfully updated metadata for artist ID: {db_artist.id}")
        metadata_provider.download_artist_cover_image(artist=updated_artist)
        return updated_artist


def auto_download_all_approved_album_requests() -> None:
    db: Session = SessionLocal() if SessionLocal else next(get_session())
    music_repository = MusicRepository(db=db)
    torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
    indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
    notification_service = NotificationService(
        notification_repository=NotificationRepository(db=db)
    )
    music_service = MusicService(
        music_repository=music_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
        notification_service=notification_service,
    )

    log.info("Auto downloading all approved album requests")
    album_requests = music_repository.get_album_requests()
    log.info(f"Found {len(album_requests)} album requests to process")
    count = 0

    for album_request in album_requests:
        if album_request.authorized:
            album = music_repository.get_album(album_id=album_request.album_id)
            artist = music_repository.get_artist_by_id(
                artist_id=ArtistId(album_request.artist.id)
            )
            if music_service.download_approved_album_request(
                album_request=album_request,
                artist=artist,
                album_name=album.name,
            ):
                count += 1
            else:
                log.info(
                    f"Could not download album request {album_request.id}"
                )

    log.info(f"Auto downloaded {count} approved album requests")
    db.commit()
    db.close()


def import_all_music_torrents() -> None:
    with next(get_session()) as db:
        music_repository = MusicRepository(db=db)
        torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
        indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
        notification_service = NotificationService(
            notification_repository=NotificationRepository(db=db)
        )
        music_service = MusicService(
            music_repository=music_repository,
            torrent_service=torrent_service,
            indexer_service=indexer_service,
            notification_service=notification_service,
        )
        log.info("Importing all music torrents")
        torrents = torrent_service.get_all_torrents()
        for t in torrents:
            try:
                if not t.imported and t.status == TorrentStatus.finished:
                    artist = music_repository.get_artist_by_torrent_id(
                        torrent_id=t.id
                    )
                    if artist is None:
                        continue
                    music_service.import_music_files(torrent=t, artist=artist)
            except RuntimeError:
                log.exception(f"Failed to import torrent {t.title}")
        log.info("Finished importing all music torrents")
        db.commit()


def update_all_artists_metadata() -> None:
    with next(get_session()) as db:
        music_repository = MusicRepository(db=db)
        music_service = MusicService(
            music_repository=music_repository,
            torrent_service=TorrentService(
                torrent_repository=TorrentRepository(db=db)
            ),
            indexer_service=IndexerService(
                indexer_repository=IndexerRepository(db=db)
            ),
            notification_service=NotificationService(
                notification_repository=NotificationRepository(db=db)
            ),
        )

        log.info("Updating metadata for all artists")
        artists = music_repository.get_artists()
        log.info(f"Found {len(artists)} artists to update")

        for artist in artists:
            try:
                if artist.metadata_provider == "musicbrainz":
                    metadata_provider = MusicBrainzMetadataProvider()
                else:
                    log.error(
                        f"Unsupported metadata provider {artist.metadata_provider} for artist {artist.name}, skipping update."
                    )
                    continue
            except Exception:
                log.exception(
                    f"Error initializing metadata provider {artist.metadata_provider} for artist {artist.name}",
                )
                continue
            music_service.update_artist_metadata(
                db_artist=artist, metadata_provider=metadata_provider
            )
        db.commit()
