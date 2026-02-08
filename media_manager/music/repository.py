import logging

from sqlalchemy import delete, select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session, joinedload

from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.music.models import Album, AlbumFile, AlbumRequest, Artist
from media_manager.music.schemas import (
    AlbumFile as AlbumFileSchema,
)
from media_manager.music.schemas import (
    AlbumId,
    AlbumRequestId,
    AlbumTorrent as AlbumTorrentSchema,
)
from media_manager.music.schemas import (
    AlbumRequest as AlbumRequestSchema,
)
from media_manager.music.schemas import (
    Artist as ArtistSchema,
)
from media_manager.music.schemas import (
    ArtistId,
)
from media_manager.music.schemas import (
    RichAlbumRequest as RichAlbumRequestSchema,
)
from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import TorrentId

log = logging.getLogger(__name__)


class MusicRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_artist_by_id(self, artist_id: ArtistId) -> ArtistSchema:
        try:
            stmt = (
                select(Artist)
                .options(joinedload(Artist.albums).joinedload(Album.tracks))
                .where(Artist.id == artist_id)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Artist with id {artist_id} not found."
                raise NotFoundError(msg)
            return ArtistSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while retrieving artist {artist_id}")
            raise

    def get_artist_by_external_id(
        self, external_id: str, metadata_provider: str
    ) -> ArtistSchema:
        try:
            stmt = (
                select(Artist)
                .options(joinedload(Artist.albums).joinedload(Album.tracks))
                .where(Artist.external_id == external_id)
                .where(Artist.metadata_provider == metadata_provider)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Artist with external_id {external_id} and provider {metadata_provider} not found."
                raise NotFoundError(msg)
            return ArtistSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error while retrieving artist by external_id {external_id}"
            )
            raise

    def get_artists(self) -> list[ArtistSchema]:
        try:
            stmt = select(Artist).options(
                joinedload(Artist.albums).joinedload(Album.tracks)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [ArtistSchema.model_validate(artist) for artist in results]
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while retrieving all artists")
            raise

    def save_artist(self, artist: ArtistSchema) -> ArtistSchema:
        log.debug(f"Attempting to save artist: {artist.name} (ID: {artist.id})")
        db_artist = self.db.get(Artist, artist.id) if artist.id else None

        if db_artist:
            log.debug(f"Updating existing artist with ID: {artist.id}")
            db_artist.external_id = artist.external_id
            db_artist.metadata_provider = artist.metadata_provider
            db_artist.name = artist.name
            db_artist.overview = artist.overview
            db_artist.country = artist.country
            db_artist.disambiguation = artist.disambiguation
        else:
            log.debug(f"Creating new artist: {artist.name}")
            artist_data = artist.model_dump(exclude={"albums"})
            db_artist = Artist(**artist_data)
            self.db.add(db_artist)

            for album in artist.albums:
                album_data = album.model_dump(exclude={"tracks"})
                album_data["artist_id"] = db_artist.id
                db_album = Album(**album_data)
                self.db.add(db_album)

                for track in album.tracks:
                    from media_manager.music.models import Track

                    track_data = track.model_dump()
                    track_data["album_id"] = db_album.id
                    db_track = Track(**track_data)
                    self.db.add(db_track)

        try:
            self.db.commit()
            self.db.refresh(db_artist)
            log.info(f"Successfully saved artist: {db_artist.name} (ID: {db_artist.id})")
            return self.get_artist_by_id(ArtistId(db_artist.id))
        except IntegrityError as e:
            self.db.rollback()
            log.exception(f"Integrity error while saving artist {artist.name}")
            msg = f"Artist with this primary key or unique constraint violation: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while saving artist {artist.name}")
            raise

    def delete_artist(self, artist_id: ArtistId) -> None:
        log.debug(f"Attempting to delete artist with id: {artist_id}")
        try:
            artist = self.db.get(Artist, artist_id)
            if not artist:
                log.warning(f"Artist with id {artist_id} not found for deletion.")
                msg = f"Artist with id {artist_id} not found."
                raise NotFoundError(msg)
            self.db.delete(artist)
            self.db.commit()
            log.info(f"Successfully deleted artist with id: {artist_id}")
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while deleting artist {artist_id}")
            raise

    def set_artist_library(self, artist_id: ArtistId, library: str) -> None:
        try:
            artist = self.db.get(Artist, artist_id)
            if not artist:
                msg = f"Artist with id {artist_id} not found."
                raise NotFoundError(msg)
            artist.library = library
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error setting library for artist {artist_id}")
            raise

    def update_artist_attributes(
        self,
        artist_id: ArtistId,
        name: str | None = None,
        overview: str | None = None,
        country: str | None = None,
        disambiguation: str | None = None,
    ) -> ArtistSchema:
        db_artist = self.db.get(Artist, artist_id)
        if not db_artist:
            msg = f"Artist with id {artist_id} not found."
            raise NotFoundError(msg)

        updated = False
        if name is not None and db_artist.name != name:
            db_artist.name = name
            updated = True
        if overview is not None and db_artist.overview != overview:
            db_artist.overview = overview
            updated = True
        if country is not None and db_artist.country != country:
            db_artist.country = country
            updated = True
        if disambiguation is not None and db_artist.disambiguation != disambiguation:
            db_artist.disambiguation = disambiguation
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_artist)
        return self.get_artist_by_id(ArtistId(db_artist.id))

    def get_album(self, album_id: AlbumId) -> "Album":
        from media_manager.music.schemas import Album as AlbumSchema

        try:
            stmt = (
                select(Album)
                .options(joinedload(Album.tracks))
                .where(Album.id == album_id)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Album with id {album_id} not found."
                raise NotFoundError(msg)
            return AlbumSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while retrieving album {album_id}")
            raise

    # -------------------------------------------------------------------------
    # ALBUM REQUESTS
    # -------------------------------------------------------------------------

    def add_album_request(
        self, album_request: AlbumRequestSchema
    ) -> AlbumRequestSchema:
        db_model = AlbumRequest(
            id=album_request.id,
            album_id=album_request.album_id,
            requested_by_id=album_request.requested_by.id
            if album_request.requested_by
            else None,
            authorized_by_id=album_request.authorized_by.id
            if album_request.authorized_by
            else None,
            wanted_quality=album_request.wanted_quality,
            min_quality=album_request.min_quality,
            authorized=album_request.authorized,
        )
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            log.info(f"Successfully added album request with id: {db_model.id}")
            return AlbumRequestSchema.model_validate(db_model)
        except IntegrityError:
            self.db.rollback()
            log.exception("Integrity error while adding album request")
            raise
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while adding album request")
            raise

    def delete_album_request(self, album_request_id: AlbumRequestId) -> None:
        try:
            stmt = delete(AlbumRequest).where(AlbumRequest.id == album_request_id)
            result = self.db.execute(stmt)
            if result.rowcount == 0:
                self.db.rollback()
                msg = f"Album request with id {album_request_id} not found."
                raise NotFoundError(msg)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error while deleting album request {album_request_id}"
            )
            raise

    def get_album_requests(self) -> list[RichAlbumRequestSchema]:
        try:
            stmt = select(AlbumRequest).options(
                joinedload(AlbumRequest.requested_by),
                joinedload(AlbumRequest.authorized_by),
                joinedload(AlbumRequest.album).joinedload(Album.artist),
            )
            results = self.db.execute(stmt).scalars().unique().all()
            rich_results = []
            for req in results:
                album_schema = self.get_album(AlbumId(req.album_id))
                artist_schema = self.get_artist_by_id(ArtistId(req.album.artist_id))
                rich_results.append(
                    RichAlbumRequestSchema(
                        id=req.id,
                        album_id=req.album_id,
                        wanted_quality=req.wanted_quality,
                        min_quality=req.min_quality,
                        requested_by=req.requested_by,
                        authorized=req.authorized,
                        authorized_by=req.authorized_by,
                        album=album_schema,
                        artist=artist_schema,
                    )
                )
            return rich_results
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while retrieving album requests")
            raise

    def get_album_request(self, album_request_id: AlbumRequestId) -> AlbumRequestSchema:
        try:
            request = self.db.get(AlbumRequest, album_request_id)
            if not request:
                msg = f"Album request with id {album_request_id} not found."
                raise NotFoundError(msg)
            return AlbumRequestSchema.model_validate(request)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error retrieving album request {album_request_id}")
            raise

    # -------------------------------------------------------------------------
    # ALBUM FILES
    # -------------------------------------------------------------------------

    def add_album_file(self, album_file: AlbumFileSchema) -> AlbumFileSchema:
        db_model = AlbumFile(**album_file.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            return AlbumFileSchema.model_validate(db_model)
        except IntegrityError:
            self.db.rollback()
            log.exception("Integrity error while adding album file")
            raise
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while adding album file")
            raise

    def remove_album_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        try:
            stmt = delete(AlbumFile).where(AlbumFile.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error removing album files for torrent_id {torrent_id}"
            )
            raise
        return result.rowcount

    def get_album_files_by_album_id(self, album_id: AlbumId) -> list[AlbumFileSchema]:
        try:
            stmt = select(AlbumFile).where(AlbumFile.album_id == album_id)
            results = self.db.execute(stmt).scalars().all()
            return [AlbumFileSchema.model_validate(af) for af in results]
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error retrieving album files for album_id {album_id}"
            )
            raise

    # -------------------------------------------------------------------------
    # TORRENTS
    # -------------------------------------------------------------------------

    def get_torrents_by_artist_id(
        self, artist_id: ArtistId
    ) -> list[AlbumTorrentSchema]:
        try:
            stmt = (
                select(Torrent, AlbumFile.file_path_suffix)
                .distinct()
                .join(AlbumFile, AlbumFile.torrent_id == Torrent.id)
                .join(Album, Album.id == AlbumFile.album_id)
                .where(Album.artist_id == artist_id)
            )
            results = self.db.execute(stmt).all()
            formatted_results = []
            for torrent, file_path_suffix in results:
                album_torrent = AlbumTorrentSchema(
                    torrent_id=torrent.id,
                    torrent_title=torrent.title,
                    status=torrent.status,
                    quality=torrent.quality,
                    imported=torrent.imported,
                    file_path_suffix=file_path_suffix,
                    usenet=torrent.usenet,
                )
                formatted_results.append(album_torrent)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error retrieving torrents for artist_id {artist_id}"
            )
            raise
        return formatted_results

    def get_all_artists_with_torrents(self) -> list[ArtistSchema]:
        try:
            stmt = (
                select(Artist)
                .distinct()
                .join(Album, Artist.id == Album.artist_id)
                .join(AlbumFile, Album.id == AlbumFile.album_id)
                .join(Torrent, AlbumFile.torrent_id == Torrent.id)
                .options(joinedload(Artist.albums).joinedload(Album.tracks))
                .order_by(Artist.name)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [ArtistSchema.model_validate(artist) for artist in results]
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error retrieving all artists with torrents")
            raise

    def get_artist_by_torrent_id(self, torrent_id: TorrentId) -> ArtistSchema | None:
        try:
            stmt = (
                select(Artist)
                .join(Album, Artist.id == Album.artist_id)
                .join(AlbumFile, Album.id == AlbumFile.album_id)
                .where(AlbumFile.torrent_id == torrent_id)
                .options(joinedload(Artist.albums).joinedload(Album.tracks))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                return None
            return ArtistSchema.model_validate(result)
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error retrieving artist by torrent_id {torrent_id}"
            )
            raise
