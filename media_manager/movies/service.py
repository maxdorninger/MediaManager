import re
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from media_manager.config import AllEncompassingConfig
from media_manager.exceptions import InvalidConfigError
from media_manager.indexer.repository import IndexerRepository
from media_manager.database import SessionLocal, get_session
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.indexer.schemas import IndexerQueryResultId
from media_manager.indexer.utils import evaluate_indexer_query_results
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.notification.service import NotificationService
from media_manager.torrent.schemas import Torrent, TorrentStatus
from media_manager.torrent.service import TorrentService
from media_manager.movies import log
from media_manager.movies.schemas import (
    Movie,
    MovieId,
    MovieRequest,
    MovieFile,
    RichMovieTorrent,
    PublicMovie,
    PublicMovieFile,
    MovieRequestId,
    RichMovieRequest,
)
from media_manager.torrent.schemas import QualityStrings
from media_manager.movies.repository import MovieRepository
from media_manager.exceptions import NotFoundError
import pprint
from media_manager.torrent.repository import TorrentRepository
from media_manager.torrent.utils import (
    import_file,
    import_torrent,
    remove_special_characters,
)
from media_manager.indexer.service import IndexerService
from media_manager.metadataProvider.abstractMetaDataProvider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.tmdb import TmdbMetadataProvider
from media_manager.metadataProvider.tvdb import TvdbMetadataProvider


class MovieService:
    def __init__(
        self,
        movie_repository: MovieRepository,
        torrent_service: TorrentService,
        indexer_service: IndexerService,
        notification_service: NotificationService = None,
    ):
        self.movie_repository = movie_repository
        self.torrent_service = torrent_service
        self.indexer_service = indexer_service
        self.notification_service = notification_service

    def add_movie(
        self, external_id: int, metadata_provider: AbstractMetadataProvider
    ) -> Movie | None:
        """
        Add a new movie to the database.

        :param external_id: The ID of the movie in the metadata provider's system.
        :param metadata_provider: The name of the metadata provider.
        """
        movie_with_metadata = metadata_provider.get_movie_metadata(id=external_id)
        saved_movie = self.movie_repository.save_movie(movie=movie_with_metadata)
        metadata_provider.download_movie_poster_image(movie=saved_movie)
        return saved_movie

    def add_movie_request(self, movie_request: MovieRequest) -> MovieRequest:
        """
        Add a new movie request.

        :param movie_request: The movie request to add.
        :return: The added movie request.
        """
        return self.movie_repository.add_movie_request(movie_request=movie_request)

    def get_movie_request_by_id(
        self, movie_request_id: MovieRequestId
    ) -> MovieRequest | None:
        """
        Get a movie request by its ID.

        :param movie_request_id: The ID of the movie request.
        :return: The movie request or None if not found.
        """
        return self.movie_repository.get_movie_request(
            movie_request_id=movie_request_id
        )

    def update_movie_request(self, movie_request: MovieRequest) -> MovieRequest:
        """
        Update an existing movie request.

        :param movie_request: The movie request to update.
        :return: The updated movie request.
        """
        self.movie_repository.delete_movie_request(movie_request_id=movie_request.id)
        return self.movie_repository.add_movie_request(movie_request=movie_request)

    def delete_movie_request(self, movie_request_id: MovieRequestId) -> None:
        """
        Delete a movie request by its ID.

        :param movie_request_id: The ID of the movie request to delete.
        """
        self.movie_repository.delete_movie_request(movie_request_id=movie_request_id)

    def get_public_movie_files_by_movie_id(
        self, movie_id: MovieId
    ) -> list[PublicMovieFile]:
        """
        Get all public movie files for a given movie ID.

        :param movie_id: The ID of the movie.
        :return: A list of public movie files.
        """
        movie_files = self.movie_repository.get_movie_files_by_movie_id(
            movie_id=movie_id
        )
        public_movie_files = [PublicMovieFile.model_validate(x) for x in movie_files]
        result = []
        for movie_file in public_movie_files:
            if self.movie_file_exists_on_file(movie_file=movie_file):
                movie_file.downloaded = True
            result.append(movie_file)
        return result

    def check_if_movie_exists(
        self,
        external_id: int = None,
        metadata_provider: str = None,
        movie_id: MovieId = None,
    ) -> bool:
        """
        Check if a movie exists in the database.

        :param external_id: The external ID of the movie.
        :param metadata_provider: The metadata provider.
        :param movie_id: The ID of the movie.
        :return: True if the movie exists, False otherwise.
        :raises ValueError: If neither external ID and metadata provider nor movie ID are provided.
        """
        if external_id and metadata_provider:
            try:
                self.movie_repository.get_movie_by_external_id(
                    external_id=external_id, metadata_provider=metadata_provider
                )
                return True
            except NotFoundError:
                return False
        elif movie_id:
            try:
                self.movie_repository.get_movie_by_id(movie_id=movie_id)
                return True
            except NotFoundError:
                return False
        else:
            raise ValueError(
                "External ID and metadata provider or Movie ID must be provided"
            )

    def get_all_available_torrents_for_a_movie(
        self, movie_id: MovieId, search_query_override: str = None
    ) -> list[IndexerQueryResult]:
        """
        Get all available torrents for a given movie.

        :param movie_id: The ID of the movie.
        :param search_query_override: Optional override for the search query.
        :return: A list of indexer query results.
        """
        log.debug(f"getting all available torrents for movie {movie_id}")
        movie = self.movie_repository.get_movie_by_id(movie_id=movie_id)
        if search_query_override:
            search_query = search_query_override
        else:
            search_query = f"{movie.name}"

        torrents: list[IndexerQueryResult] = self.indexer_service.search(
            query=search_query, is_tv=False
        )

        if search_query_override:
            log.debug(
                f"Found with search query override {torrents.__len__()} torrents: {torrents}"
            )
            return torrents

        result: list[IndexerQueryResult] = []
        for torrent in torrents:
            if (
                movie.name.lower() in torrent.title.lower()
                and str(movie.year) in torrent.title
            ):
                result.append(torrent)

        return evaluate_indexer_query_results(
            is_tv=False, query_results=result, media=movie
        )

    def get_all_movies(self) -> list[Movie]:
        """
        Get all movies.

        :return: A list of all movies.
        """
        return self.movie_repository.get_movies()

    def search_for_movie(
        self, query: str, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        """
        Search for movies using a given query.

        :param query: The search query.
        :param metadata_provider: The metadata provider to search.
        :return: A list of metadata provider movie search results.
        """
        results = metadata_provider.search_movie(query)
        for result in results:
            if self.check_if_movie_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            ):
                result.added = True
        return results

    def get_popular_movies(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        """
        Get popular movies from a given metadata provider.

        :param metadata_provider: The metadata provider to use.
        :return: A list of metadata provider movie search results.
        """
        results: list[MetaDataProviderSearchResult] = metadata_provider.search_movie()

        filtered_results = []
        for result in results:
            if not self.check_if_movie_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            ):
                filtered_results.append(result)

        return filtered_results

    def get_public_movie_by_id(self, movie_id: MovieId) -> PublicMovie:
        """
        Get a public movie by its ID.

        :param movie_id: The ID of the movie.
        :return: A public movie.
        """
        movie = self.movie_repository.get_movie_by_id(movie_id=movie_id)
        torrents = self.get_torrents_for_movie(movie=movie).torrents
        public_movie = PublicMovie.model_validate(movie)
        public_movie.downloaded = self.is_movie_downloaded(movie_id=movie.id)
        public_movie.torrents = torrents
        return public_movie

    def get_movie_by_id(self, movie_id: MovieId) -> Movie:
        """
        Get a movie by its ID.

        :param movie_id: The ID of the movie.
        :return: The movie.
        """
        return self.movie_repository.get_movie_by_id(movie_id=movie_id)

    def is_movie_downloaded(self, movie_id: MovieId) -> bool:
        """
        Check if a movie is downloaded.

        :param movie_id: The ID of the movie.
        :return: True if the movie is downloaded, False otherwise.
        """
        movie_files = self.movie_repository.get_movie_files_by_movie_id(
            movie_id=movie_id
        )
        for movie_file in movie_files:
            if self.movie_file_exists_on_file(movie_file=movie_file):
                return True
        return False

    def movie_file_exists_on_file(self, movie_file: MovieFile) -> bool:
        """
        Check if a movie file exists on the filesystem.

        :param movie_file: The movie file to check.
        :return: True if the file exists, False otherwise.
        """
        if movie_file.torrent_id is None:
            return True
        else:
            torrent_file = self.torrent_service.get_torrent_by_id(
                torrent_id=movie_file.torrent_id
            )
            if torrent_file.imported:
                return True
        return False

    def get_movie_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> Movie | None:
        """
        Get a movie by its external ID and metadata provider.

        :param external_id: The external ID of the movie.
        :param metadata_provider: The metadata provider.
        :return: The movie or None if not found.
        """
        return self.movie_repository.get_movie_by_external_id(
            external_id=external_id, metadata_provider=metadata_provider
        )

    def get_all_movie_requests(self) -> list[RichMovieRequest]:
        """
        Get all movie requests.

        :return: A list of rich movie requests.
        """
        return self.movie_repository.get_movie_requests()

    def set_movie_library(self, movie_id: MovieId, library: str) -> None:
        self.movie_repository.set_movie_library(movie_id=movie_id, library=library)

    def get_torrents_for_movie(self, movie: Movie) -> RichMovieTorrent:
        """
        Get torrents for a given movie.

        :param movie: The movie.
        :return: A rich movie torrent.
        """
        movie_torrents = self.movie_repository.get_torrents_by_movie_id(
            movie_id=movie.id
        )
        return RichMovieTorrent(
            movie_id=movie.id,
            name=movie.name,
            year=movie.year,
            metadata_provider=movie.metadata_provider,
            torrents=movie_torrents,
        )

    def get_all_movies_with_torrents(self) -> list[RichMovieTorrent]:
        """
        Get all movies with torrents.

        :return: A list of rich movie torrents.
        """
        movies = self.movie_repository.get_all_movies_with_torrents()
        return [self.get_torrents_for_movie(movie=movie) for movie in movies]

    def download_torrent(
        self,
        public_indexer_result_id: IndexerQueryResultId,
        movie_id: MovieId,
        override_movie_file_path_suffix: str = "",
    ) -> Torrent:
        """
        Download a torrent for a given indexer result and movie.

        :param public_indexer_result_id: The ID of the indexer result.
        :param movie_id: The ID of the movie.
        :param override_movie_file_path_suffix: Optional override for the file path suffix.
        :return: The downloaded torrent.
        """
        indexer_result = self.indexer_service.get_result(
            result_id=public_indexer_result_id
        )
        movie_torrent = self.torrent_service.download(indexer_result=indexer_result)

        movie_file = MovieFile(
            movie_id=movie_id,
            quality=indexer_result.quality,
            torrent_id=movie_torrent.id,
            file_path_suffix=override_movie_file_path_suffix,
        )
        self.movie_repository.add_movie_file(movie_file=movie_file)
        return movie_torrent

    def download_approved_movie_request(
        self, movie_request: MovieRequest, movie: Movie
    ) -> bool:
        """
        Download an approved movie request.

        :param movie_request: The movie request to download.
        :param movie: The Movie object.
        :return: True if the download was successful, False otherwise.
        :raises ValueError: If the movie request is not authorized.
        """
        if not movie_request.authorized:
            log.error(
                f"Movie request {movie_request.id} is not authorized for download"
            )
            raise ValueError(
                f"Movie request {movie_request.id} is not authorized for download"
            )

        log.info(f"Downloading approved movie request {movie_request.id}")

        torrents = self.get_all_available_torrents_for_a_movie(movie_id=movie.id)
        available_torrents: list[IndexerQueryResult] = []

        for torrent in torrents:
            if (
                (torrent.quality.value < movie_request.wanted_quality.value)
                or (torrent.quality.value > movie_request.min_quality.value)
                or (torrent.seeders < 3)
            ):
                log.info(
                    f"Skipping torrent {torrent.title} with quality {torrent.quality} for movie {movie.id}, because it does not match the requested quality {movie_request.wanted_quality}"
                )
            else:
                available_torrents.append(torrent)
                log.info(
                    f"Taking torrent {torrent.title} with quality {torrent.quality} for movie {movie.id} into consideration"
                )

        if len(available_torrents) == 0:
            log.warning(
                f"No torrents matching criteria were found (wanted quality: {movie_request.wanted_quality}, min_quality: {movie_request.min_quality} for movie {movie.id})"
            )
            return False

        available_torrents.sort()

        torrent = self.torrent_service.download(indexer_result=available_torrents[0])
        movie_file = MovieFile(
            movie_id=movie.id,
            quality=torrent.quality,
            torrent_id=torrent.id,
            file_path_suffix=QualityStrings[torrent.quality.name].value.upper(),
        )
        try:
            self.movie_repository.add_movie_file(movie_file=movie_file)
        except IntegrityError:
            log.warning(
                f"Movie file for movie {movie.id} and quality {torrent.quality} already exists, skipping."
            )
        self.delete_movie_request(movie_request.id)
        return True

    def import_torrent_files(self, torrent: Torrent, movie: Movie) -> None:
        """
        Organizes files from a torrent into the movie directory structure.
        :param torrent: The Torrent object
        :param movie: The Movie object
        """

        video_files, subtitle_files, all_files = import_torrent(torrent=torrent)
        success: bool = False  # determines if the import was successful, if true, the Imported flag will be set to True after the import

        if len(video_files) != 0:
            # Send notification about multiple video files found
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Multiple Video Files Found",
                    message=f"Found {len(video_files)} video files in movie torrent '{torrent.title}' for {movie.name} ({movie.year}). Only the first will be imported. Manual intervention recommended.",
                )
            log.error(
                "Found multiple video files in movie torrent, only the first will be imported. Manual intervention is recommended.."
            )
        log.info(
            f"Importing these {len(video_files) + len(subtitle_files)} files:\n"
            + pprint.pformat(video_files)
            + "\n"
            + pprint.pformat(subtitle_files)
        )
        misc_config = AllEncompassingConfig().misc

        movie_file_path = (
            misc_config.movie_directory
            / f"{remove_special_characters(movie.name)} ({movie.year})  [{movie.metadata_provider}id-{movie.external_id}]"
        )
        log.debug(
            f"Movie {movie.name} without special characters: {remove_special_characters(movie.name)}"
        )
        if movie.library != "Default":
            for library in misc_config.movie_libraries:
                if library.name == movie.library:
                    log.debug(f"Using library {library.name} for movie {movie.name}")
                    movie_file_path = (
                        Path(library.path)
                        / f"{remove_special_characters(movie.name)} ({movie.year})  [{movie.metadata_provider}id-{movie.external_id}]"
                    )
                    break
            else:
                log.warning(
                    f"Movie library {movie.library} not found in config, using default movie directory."
                )

        movie_files: list[MovieFile] = self.torrent_service.get_movie_files_of_torrent(
            torrent=torrent
        )
        log.info(
            f"Found {len(movie_files)} movie files associated with torrent {torrent.title}"
        )

        for movie_file in movie_files:
            try:
                movie_file_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                log.warning(f"Could not create path {movie_file_path}: {e}")

            movie_file_name = f"{remove_special_characters(movie.name)} ({movie.year})"
            if movie_file.file_path_suffix != "":
                movie_file_name += f" - {movie_file.file_path_suffix}"

            # import movie video
            if video_files:
                target_video_file = (
                    movie_file_path / f"{movie_file_name}{video_files[0].suffix}"
                )
                import_file(target_file=target_video_file, source_file=video_files[0])
                success = True

            # import subtitles
            for subtitle_file in subtitle_files:
                language_code_match = re.search(
                    r"[. ]([a-z]{2})\.srt$", subtitle_file.name, re.IGNORECASE
                )
                if not language_code_match:
                    log.warning(
                        f"Subtitle file {subtitle_file.name} does not match expected format, can't extract language code, skipping."
                    )
                    continue
                language_code = language_code_match.group(1)
                target_subtitle_file = (
                    movie_file_path / f"{movie_file_name}.{language_code}.srt"
                )
                import_file(target_file=target_subtitle_file, source_file=subtitle_file)

        if success:
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)

            # Send successful import notification
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Movie Downloaded",
                    message=f"Successfully downloaded: {movie.name} ({movie.year}) from torrent {torrent.title}.",
                )

        log.info(f"Finished organizing files for torrent {torrent.title}")

    def update_movie_metadata(
        self, db_movie: Movie, metadata_provider: AbstractMetadataProvider
    ) -> Movie | None:
        """
        Updates the metadata of a movie.

        :param metadata_provider: The metadata provider object to fetch fresh data from.
        :param db_movie: The Movie to update
        :return: The updated Movie object, or None if the movie is not found or an error occurs.
        """
        log.debug(f"Found movie: {db_movie.name} for metadata update.")

        fresh_movie_data = metadata_provider.get_movie_metadata(id=db_movie.external_id)
        if not fresh_movie_data:
            log.warning(
                f"Could not fetch fresh metadata for movie {db_movie.name} (External ID: {db_movie.external_id}) from {db_movie.metadata_provider}."
            )
            return db_movie
        log.debug(f"Fetched fresh metadata for movie: {fresh_movie_data.name}")

        self.movie_repository.update_movie_attributes(
            movie_id=db_movie.id,
            name=fresh_movie_data.name,
            overview=fresh_movie_data.overview,
            year=fresh_movie_data.year,
        )

        updated_movie = self.movie_repository.get_movie_by_id(movie_id=db_movie.id)

        log.info(f"Successfully updated metadata for movie ID: {db_movie.id}")
        metadata_provider.download_movie_poster_image(movie=updated_movie)
        return updated_movie


def auto_download_all_approved_movie_requests() -> None:
    """
    Auto download all approved movie requests.
    This is a standalone function as it creates its own DB session.
    """
    db: Session = SessionLocal()
    movie_repository = MovieRepository(db=db)
    torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
    indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
    movie_service = MovieService(
        movie_repository=movie_repository,
        torrent_service=torrent_service,
        indexer_service=indexer_service,
    )

    log.info("Auto downloading all approved movie requests")
    movie_requests = movie_repository.get_movie_requests()
    log.info(f"Found {len(movie_requests)} movie requests to process")
    log.debug(f"Movie requests:  {[x.model_dump() for x in movie_requests]}")
    count = 0

    for movie_request in movie_requests:
        if movie_request.authorized:
            log.info(f"Processing movie request {movie_request.id} for download")
            movie = movie_repository.get_movie_by_id(movie_id=movie_request.movie_id)
            if movie_service.download_approved_movie_request(
                movie_request=movie_request, movie=movie
            ):
                count += 1
            else:
                log.warning(
                    f"Failed to download movie request {movie_request.id} for movie {movie.name}"
                )

    log.info(f"Auto downloaded {count} approved movie requests")
    db.commit()
    db.close()


def import_all_movie_torrents() -> None:
    with next(get_session()) as db:
        movie_repository = MovieRepository(db=db)
        torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
        indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
        movie_service = MovieService(
            movie_repository=movie_repository,
            torrent_service=torrent_service,
            indexer_service=indexer_service,
        )
        log.info("Importing all torrents")
        torrents = torrent_service.get_all_torrents()
        log.info("Found %d torrents to import", len(torrents))
        for t in torrents:
            try:
                if not t.imported and t.status == TorrentStatus.finished:
                    movie = torrent_service.get_movie_of_torrent(torrent=t)
                    if movie is None:
                        log.warning(
                            f"torrent {t.title} is not a movie torrent, skipping import."
                        )
                        continue
                    movie_service.import_torrent_files(torrent=t, movie=movie)
            except RuntimeError as e:
                log.error(
                    f"Error importing torrent {t.title} for movie {movie.name}: {e}"
                )
        log.info("Finished importing all torrents")
        db.commit()


def update_all_movies_metadata() -> None:
    """
    Updates the metadata of all movies.
    """
    with next(get_session()) as db:
        movie_repository = MovieRepository(db=db)
        movie_service = MovieService(
            movie_repository=movie_repository,
            torrent_service=TorrentService(torrent_repository=TorrentRepository(db=db)),
            indexer_service=IndexerService(indexer_repository=IndexerRepository(db=db)),
        )

        log.info("Updating metadata for all movies")

        movies = movie_repository.get_movies()

        log.info(f"Found {len(movies)} movies to update")

        for movie in movies:
            try:
                if movie.metadata_provider == "tmdb":
                    metadata_provider = TmdbMetadataProvider()
                elif movie.metadata_provider == "tvdb":
                    metadata_provider = TvdbMetadataProvider()
                else:
                    log.error(
                        f"Unsupported metadata provider {movie.metadata_provider} for movie {movie.name}, skipping update."
                    )
                    continue
            except InvalidConfigError as e:
                log.error(
                    f"Error initializing metadata provider {movie.metadata_provider} for movie {movie.name}: {str(e)}"
                )
                continue
            updated_movie = movie_service.update_movie_metadata(
                db_movie=movie, metadata_provider=metadata_provider
            )

            if updated_movie:
                log.info(
                    f"Successfully updated metadata for movie: {updated_movie.name}"
                )
            else:
                log.warning(f"Failed to update metadata for movie: {movie.name}")
        db.commit()
