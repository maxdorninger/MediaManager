import logging

from media_manager.common.service import BaseMetadataService
from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.metadataProvider.tmdb import TmdbMetadataProvider
from media_manager.metadataProvider.tvdb import TvdbMetadataProvider
from media_manager.movies.repository import MovieRepository
from media_manager.movies.schemas import Movie

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
        """
        log.debug(f"Found movie: {db_movie.name} for metadata update.")
        fresh_movie_data = metadata_provider.get_movie_metadata(
            movie_id=db_movie.external_id, language=db_movie.original_language
        )
        if not fresh_movie_data:
            log.warning(f"Could not fetch fresh metadata for movie: {db_movie.name}")
            return None

        self.movie_repository.update_movie_attributes(
            movie_id=db_movie.id,
            name=fresh_movie_data.name,
            overview=fresh_movie_data.overview,
            year=fresh_movie_data.year,
            imdb_id=fresh_movie_data.imdb_id,
        )
        updated_movie = self.movie_repository.get_movie_by_id(db_movie.id)
        metadata_provider.download_movie_poster_image(movie=updated_movie)
        return updated_movie

    def update_all_metadata(self) -> None:
        self.update_all_metadata_base(
            get_all_to_update_func=self.movie_repository.get_movies,
            update_single_func=self.update_movie_metadata,
            tmdb_provider_class=TmdbMetadataProvider,
            tvdb_provider_class=TvdbMetadataProvider,
            media_type_name="movie",
        )
