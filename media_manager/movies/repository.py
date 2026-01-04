from sqlalchemy import select, delete
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session, joinedload
import logging

from media_manager.exceptions import NotFoundError, ConflictError
from media_manager.movies.models import Movie, MovieRequest, MovieFile
from media_manager.movies.schemas import (
    Movie as MovieSchema,
    MovieId,
    MovieRequest as MovieRequestSchema,
    MovieRequestId,
    MovieFile as MovieFileSchema,
    RichMovieRequest as RichMovieRequestSchema,
    MovieTorrent as MovieTorrentSchema,
)
from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import TorrentId

log = logging.getLogger(__name__)


class MovieRepository:
    """
    Repository for managing movies in the database.
    Provides methods to retrieve, save, and delete movies.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_movie_by_id(self, movie_id: MovieId) -> MovieSchema:
        """
        Retrieve a movie by its ID.

        :param movie_id: The ID of the movie to retrieve.
        :return: A Movie object if found.
        :raises NotFoundError: If the movie with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(Movie).where(Movie.id == movie_id)
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                raise NotFoundError(f"Movie with id {movie_id} not found.")
            return MovieSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving movie {movie_id}: {e}")
            raise

    def get_movie_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> MovieSchema:
        """
        Retrieve a movie by its external ID.

        :param external_id: The ID of the movie to retrieve.
        :param metadata_provider: The metadata provider associated with the ID.
        :return: A Movie object if found.
        :raises NotFoundError: If the movie with the given external ID and provider is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Movie)
                .where(Movie.external_id == external_id)
                .where(Movie.metadata_provider == metadata_provider)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                raise NotFoundError(
                    f"Movie with external_id {external_id} and provider {metadata_provider} not found."
                )
            return MovieSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(
                f"Database error while retrieving movie by external_id {external_id}: {e}"
            )
            raise

    def get_movies(self) -> list[MovieSchema]:
        """
        Retrieve all movies from the database.

        :return: A list of Movie objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(Movie)
            results = self.db.execute(stmt).scalars().unique().all()
            return [MovieSchema.model_validate(movie) for movie in results]
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving all movies: {e}")
            raise

    def save_movie(self, movie: MovieSchema) -> MovieSchema:
        """
        Save a new movie or update an existing one in the database.

        :param movie: The Movie object to save.
        :return: The saved Movie object.
        :raises ValueError: If a movie with the same primary key already exists (on insert).
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to save movie: {movie.name} (ID: {movie.id})")
        db_movie = self.db.get(Movie, movie.id) if movie.id else None

        if db_movie:  # Update existing movie
            log.debug(f"Updating existing movie with ID: {movie.id}")
            db_movie.external_id = movie.external_id
            db_movie.metadata_provider = movie.metadata_provider
            db_movie.name = movie.name
            db_movie.overview = movie.overview
            db_movie.year = movie.year
            db_movie.original_language = movie.original_language
            db_movie.imdb_id = movie.imdb_id
        else:  # Insert new movie
            log.debug(f"Creating new movie: {movie.name}")
            db_movie = Movie(**movie.model_dump())
            self.db.add(db_movie)

        try:
            self.db.commit()
            self.db.refresh(db_movie)
            log.info(f"Successfully saved movie: {db_movie.name} (ID: {db_movie.id})")
            return MovieSchema.model_validate(db_movie)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while saving movie {movie.name}: {e}")
            raise ConflictError(
                f"Movie with this primary key or unique constraint violation: {e.orig}"
            ) from e
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while saving movie {movie.name}: {e}")
            raise

    def delete_movie(self, movie_id: MovieId) -> None:
        """
        Delete a movie by its ID.

        :param movie_id: The ID of the movie to delete.
        :raises NotFoundError: If the movie with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Attempting to delete movie with id: {movie_id}")
        try:
            movie = self.db.get(Movie, movie_id)
            if not movie:
                log.warning(f"Movie with id {movie_id} not found for deletion.")
                raise NotFoundError(f"Movie with id {movie_id} not found.")
            self.db.delete(movie)
            self.db.commit()
            log.info(f"Successfully deleted movie with id: {movie_id}")
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while deleting movie {movie_id}: {e}")
            raise

    def add_movie_request(
        self, movie_request: MovieRequestSchema
    ) -> MovieRequestSchema:
        """
        Adds a Movie to the MovieRequest table, which marks it as requested.

        :param movie_request: The MovieRequest object to add.
        :return: The added MovieRequest object.
        :raises IntegrityError: If a similar request already exists or violates constraints.
        :raises SQLAlchemyError: If a database error occurs.
        """
        log.debug(f"Adding movie request: {movie_request.model_dump_json()}")
        db_model = MovieRequest(
            id=movie_request.id,
            movie_id=movie_request.movie_id,
            requested_by_id=movie_request.requested_by.id
            if movie_request.requested_by
            else None,
            authorized_by_id=movie_request.authorized_by.id
            if movie_request.authorized_by
            else None,
            wanted_quality=movie_request.wanted_quality,
            min_quality=movie_request.min_quality,
            authorized=movie_request.authorized,
        )
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            log.info(f"Successfully added movie request with id: {db_model.id}")
            return MovieRequestSchema.model_validate(db_model)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while adding movie request: {e}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while adding movie request: {e}")
            raise

    def set_movie_library(self, movie_id: MovieId, library: str) -> None:
        """
        Sets the library for a movie.

        :param movie_id: The ID of the movie to update.
        :param library: The library path to set for the movie.
        :raises NotFoundError: If the movie with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            movie = self.db.get(Movie, movie_id)
            if not movie:
                raise NotFoundError(f"movie with id {movie_id} not found.")
            movie.library = library
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error setting library for movie {movie_id}: {e}")
            raise

    def delete_movie_request(self, movie_request_id: MovieRequestId) -> None:
        """
        Removes a MovieRequest by its ID.

        :param movie_request_id: The ID of the movie request to delete.
        :raises NotFoundError: If the movie request is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = delete(MovieRequest).where(MovieRequest.id == movie_request_id)
            result = self.db.execute(stmt)
            if result.rowcount == 0:
                self.db.rollback()
                raise NotFoundError(
                    f"movie request with id {movie_request_id} not found."
                )
            self.db.commit()
            # Successfully deleted movie request with id: {movie_request_id}
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(
                f"Database error while deleting movie request {movie_request_id}: {e}"
            )
            raise

    def get_movie_requests(self) -> list[RichMovieRequestSchema]:
        """
        Retrieve all movie requests.

        :return: A list of RichMovieRequest objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(MovieRequest).options(
                joinedload(MovieRequest.requested_by),
                joinedload(MovieRequest.authorized_by),
                joinedload(MovieRequest.movie),
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [RichMovieRequestSchema.model_validate(x) for x in results]
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving movie requests: {e}")
            raise

    def add_movie_file(self, movie_file: MovieFileSchema) -> MovieFileSchema:
        """
        Adds a movie file record to the database.

        :param movie_file: The MovieFile object to add.
        :return: The added MovieFile object.
        :raises IntegrityError: If the record violates constraints.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_model = MovieFile(**movie_file.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            return MovieFileSchema.model_validate(db_model)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while adding movie file: {e}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while adding movie file: {e}")
            raise

    def remove_movie_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        """
        Removes movie file records associated with a given torrent ID.

        :param torrent_id: The ID of the torrent whose movie files are to be removed.
        :return: The number of movie files removed.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = delete(MovieFile).where(MovieFile.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
            deleted_count = result.rowcount
            return deleted_count
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(
                f"Database error removing movie files for torrent_id {torrent_id}: {e}"
            )
            raise

    def get_movie_files_by_movie_id(self, movie_id: MovieId) -> list[MovieFileSchema]:
        """
        Retrieve all movie files for a given movie ID.

        :param movie_id: The ID of the movie.
        :return: A list of MovieFile objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(MovieFile).where(MovieFile.movie_id == movie_id)
            results = self.db.execute(stmt).scalars().all()
            return [MovieFileSchema.model_validate(sf) for sf in results]
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving movie files for movie_id {movie_id}: {e}"
            )
            raise

    def get_torrents_by_movie_id(self, movie_id: MovieId) -> list[MovieTorrentSchema]:
        """
        Retrieve all torrents associated with a given movie ID.

        :param movie_id: The ID of the movie.
        :return: A list of Torrent objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
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
            return formatted_results
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving torrents for movie_id {movie_id}: {e}"
            )
            raise

    def get_all_movies_with_torrents(self) -> list[MovieSchema]:
        """
        Retrieve all movies that are associated with a torrent, ordered alphabetically by movie name.

        :return: A list of Movie objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
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
        except SQLAlchemyError as e:
            log.error(f"Database error retrieving all movies with torrents: {e}")
            raise

    def get_movie_request(self, movie_request_id: MovieRequestId) -> MovieRequestSchema:
        """
        Retrieve a movie request by its ID.

        :param movie_request_id: The ID of the movie request.
        :return: A MovieRequest object.
        :raises NotFoundError: If the movie request is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            request = self.db.get(MovieRequest, movie_request_id)
            if not request:
                raise NotFoundError(
                    f"Movie request with id {movie_request_id} not found."
                )
            return MovieRequestSchema.model_validate(request)
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving movie request {movie_request_id}: {e}"
            )
            raise

    def get_movie_by_torrent_id(self, torrent_id: TorrentId) -> MovieSchema:
        """
        Retrieve a movie by a torrent ID.

        :param torrent_id: The ID of the torrent to retrieve the movie for.
        :return: A Movie object.
        :raises NotFoundError: If the movie for the given torrent ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Movie)
                .join(MovieFile, Movie.id == MovieFile.movie_id)
                .where(MovieFile.torrent_id == torrent_id)
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                raise NotFoundError(f"Movie for torrent_id {torrent_id} not found.")
            return MovieSchema.model_validate(result)
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving movie by torrent_id {torrent_id}: {e}"
            )
            raise

    def update_movie_attributes(
        self,
        movie_id: MovieId,
        name: str | None = None,
        overview: str | None = None,
        year: int | None = None,
        imdb_id: str | None = None,
    ) -> MovieSchema:
        """
        Update attributes of an existing movie.

        :param imdb_id: The new IMDb ID for the movie.
        :param movie_id: The ID of the movie to update.
        :param name: The new name for the movie.
        :param overview: The new overview for the movie.
        :param year: The new year for the movie.
        :return: The updated MovieSchema object.
        """
        db_movie = self.db.get(Movie, movie_id)
        if not db_movie:
            raise NotFoundError(f"Movie with id {movie_id} not found.")

        updated = False
        if name is not None and db_movie.name != name:
            db_movie.name = name
            updated = True
        if overview is not None and db_movie.overview != overview:
            db_movie.overview = overview
            updated = True
        if year is not None and db_movie.year != year:
            db_movie.year = year
            updated = True
        if imdb_id is not None and db_movie.imdb_id != imdb_id:
            db_movie.imdb_id = imdb_id
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_movie)
        return MovieSchema.model_validate(db_movie)
