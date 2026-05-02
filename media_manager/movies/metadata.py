import logging
from typing import Optional

from media_manager.common.service import BaseMetadataService
from media_manager.exceptions import InvalidConfigError, NotFoundError
from media_manager.metadataProvider.abstract_metadata_provider import AbstractMetadataProvider
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.metadataProvider.tmdb import TmdbMetadataProvider
from media_manager.metadataProvider.tvdb import TvdbMetadataProvider
from media_manager.movies.repository import MovieRepository
from media_manager.movies.schemas import Movie, MovieId

log = logging.getLogger(__name__)


class MovieMetadataService(BaseMetadataService[Movie, Movie]):
    def __init__(self, movie_repository: MovieRepository) -> None:
        super().__init__(repository=movie_repository)
        self.movie_repository = movie_repository

    def add_movie(
        self,
        external_id: int,
        metadata_provider: AbstractMetadataProvider,
        language: str | None = None,
    ) -> Movie:
        return self.add_media_base(
            external_id=external_id,
            metadata_provider=metadata_provider,
            get_metadata_func=metadata_provider.get_movie_metadata,
            save_func=self.movie_repository.save_movie,
            download_poster_func=metadata_provider.download_movie_poster_image,
            language=language,
        )

    def search_for_movie(
        self, query: str, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        return self.search_for_media_base(
            query=query,
            metadata_provider=metadata_provider,
            search_func=metadata_provider.search_movie,
            get_by_external_id_func=self.movie_repository.get_movie_by_external_id,
        )

    def get_popular_movies(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        return self.get_popular_media_base(
            metadata_provider=metadata_provider,
            search_func=metadata_provider.search_movie,
        )

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

        # Use stored original_language preference for metadata fetching
        fresh_movie_data = metadata_provider.get_movie_metadata(
            movie_id=db_movie.external_id, language=db_movie.original_language
        )
        if not fresh_movie_data:
            log.warning(
                f"Could not fetch fresh metadata for movie: {db_movie.name} ({db_movie.year})"
            )
            return None
        log.debug(f"Fetched fresh metadata for movie: {fresh_movie_data.name}")

        self.movie_repository.update_movie_attributes(
            movie_id=db_movie.id,
            name=fresh_movie_data.name,
            overview=fresh_movie_data.overview,
            year=fresh_movie_data.year,
            imdb_id=fresh_movie_data.imdb_id,
        )

        updated_movie = self.movie_repository.get_movie_by_id(movie_id=db_movie.id)

        log.info(
            f"Successfully updated metadata for movie: {db_movie.name} ({db_movie.year})"
        )
        metadata_provider.download_movie_poster_image(movie=updated_movie)
        return updated_movie

    def update_all_metadata(self) -> None:
        """Updates the metadata of all movies."""
        log.info("Updating metadata for all movies")
        movies = self.movie_repository.get_movies()
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
            except InvalidConfigError:
                log.exception(
                    f"Error initializing metadata provider {movie.metadata_provider} for movie {movie.name}",
                )
                continue
            self.update_movie_metadata(
                db_movie=movie, metadata_provider=metadata_provider
            )
