import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from media_manager.common.repository import BaseRepository
from media_manager.exceptions import NotFoundError
from media_manager.movies.models import Movie, MovieFile
from media_manager.movies.schemas import (
    Movie as MovieSchema,
)
from media_manager.movies.schemas import (
    MovieFile as MovieFileSchema,
)
from media_manager.movies.schemas import (
    MovieId,
)
from media_manager.movies.schemas import (
    MovieTorrent as MovieTorrentSchema,
)
from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import TorrentId

log = logging.getLogger(__name__)


class MovieRepository(BaseRepository[Movie, MovieSchema]):
    """
    Repository for managing movies in the database.
    Provides methods to retrieve, save, and delete movies.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, Movie, MovieSchema)

    def get_movie_by_id(self, movie_id: MovieId) -> MovieSchema:
        return self.get_by_id(entity_id=movie_id)

    def get_movie_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> MovieSchema:
        return self.get_by_external_id(
            external_id=external_id, metadata_provider=metadata_provider
        )

    def get_movies(self) -> list[MovieSchema]:
        return self.get_all()

    def delete_movie(self, movie_id: MovieId) -> None:
        self.delete(entity_id=movie_id)

    def set_movie_library(self, movie_id: MovieId, library: str) -> None:
        self.set_library(entity_id=movie_id, library=library)

    def save_movie(self, movie: MovieSchema) -> MovieSchema:
        return self.save_media_base(media_schema=movie, model_class=Movie)

    def add_movie_file(self, movie_file: MovieFileSchema) -> MovieFileSchema:
        return self.add_media_file_base(
            file_schema=movie_file, model_class=MovieFile, schema_class=MovieFileSchema
        )

    def remove_movie_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        return self.remove_files_by_torrent_id_base(
            torrent_id=torrent_id, model_class=MovieFile
        )

    def get_movie_files_by_movie_id(self, movie_id: MovieId) -> list[MovieFileSchema]:
        try:
            stmt = select(MovieFile).where(MovieFile.movie_id == movie_id)
            results = self.db.execute(stmt).scalars().all()
            return [MovieFileSchema.model_validate(sf) for sf in results]
        except SQLAlchemyError:
            log.exception(
                f"Database error retrieving movie files for movie_id {movie_id}"
            )
            raise

    def get_torrents_by_movie_id(self, movie_id: MovieId) -> list[MovieTorrentSchema]:
        try:
            stmt = (
                select(Torrent, MovieFile.file_path_suffix)
                .distinct()
                .join(MovieFile, MovieFile.torrent_id == Torrent.id)
                .where(MovieFile.movie_id == movie_id)
            )
            results = self.db.execute(stmt).all()
            formatted_results = []
            for torrent, file_path_suffix in results:
                movie_torrent = MovieTorrentSchema(
                    torrent_id=torrent.id,
                    torrent_title=torrent.title,
                    status=torrent.status,
                    quality=torrent.quality,
                    imported=torrent.imported,
                    file_path_suffix=file_path_suffix,
                    usenet=torrent.usenet,
                )
                formatted_results.append(movie_torrent)
        except SQLAlchemyError:
            log.exception(f"Database error retrieving torrents for movie_id {movie_id}")
            raise
        else:
            return formatted_results

    def get_all_movies_with_torrents(self) -> list[MovieSchema]:
        try:
            stmt = (
                select(Movie)
                .distinct()
                .join(MovieFile, Movie.id == MovieFile.movie_id)
                .join(Torrent, MovieFile.torrent_id == Torrent.id)
                .order_by(Movie.name)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [MovieSchema.model_validate(movie) for movie in results]
        except SQLAlchemyError:
            log.exception("Database error retrieving all movies with torrents")
            raise

    def get_movie_by_torrent_id(self, torrent_id: TorrentId) -> MovieSchema:
        try:
            stmt = (
                select(Movie)
                .join(MovieFile, Movie.id == MovieFile.movie_id)
                .where(MovieFile.torrent_id == torrent_id)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Movie for torrent_id {torrent_id} not found."
                raise NotFoundError(msg)
        except SQLAlchemyError:
            log.exception(f"Database error retrieving movie by torrent_id {torrent_id}")
            raise
        else:
            return MovieSchema.model_validate(result)

    def update_movie_attributes(
        self,
        movie_id: MovieId,
        name: str | None = None,
        overview: str | None = None,
        year: int | None = None,
        imdb_id: str | None = None,
    ) -> MovieSchema:
        return self.update_media_attributes_base(
            media_id=movie_id,
            model_class=Movie,
            name=name,
            overview=overview,
            year=year,
            imdb_id=imdb_id,
        )
