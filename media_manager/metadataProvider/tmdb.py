import logging
from typing import override

import requests

import media_manager.metadataProvider.utils
from media_manager.config import MediaManagerConfig
from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.movies.schemas import Movie
from media_manager.notification.manager import notification_manager
from media_manager.tv.schemas import Episode, EpisodeNumber, Season, SeasonNumber, Show

ENDED_STATUS = {"Ended", "Canceled"}

log = logging.getLogger(__name__)


class TmdbMetadataProvider(AbstractMetadataProvider):
    name = "tmdb"

    def __init__(self) -> None:
        config = MediaManagerConfig().metadata.tmdb
        self.url = config.tmdb_relay_url
        self.primary_languages = config.primary_languages
        self.default_language = config.default_language

    def __get_language_param(self, original_language: str | None) -> str:
        """
        Determine the language parameter to use for TMDB API calls.
        Returns the original language if it's in primary_languages, otherwise returns default_language.

        :param original_language: The original language code (ISO 639-1) of the media
        :return: Language parameter (ISO 639-1 format, e.g., 'en', 'no')
        """
        if original_language and original_language in self.primary_languages:
            return original_language
        return self.default_language

    def __get_show_metadata(self, show_id: int, language: str | None = None) -> dict:
        if language is None:
            language = self.default_language
        try:
            response = requests.get(
                url=f"{self.url}/tv/shows/{show_id}",
                params={"language": language},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting show metadata for ID {show_id}: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch show metadata for ID {show_id} from TMDB. Error: {e}",
                )
            raise

    def __get_show_external_ids(self, show_id: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/tv/shows/{show_id}/external_ids",
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting show external IDs for ID {show_id}: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch show external IDs for ID {show_id} from TMDB. Error: {e}",
                )
            raise

    def __get_season_metadata(
        self, show_id: int, season_number: int, language: str | None = None
    ) -> dict:
        if language is None:
            language = self.default_language
        try:
            response = requests.get(
                url=f"{self.url}/tv/shows/{show_id}/{season_number}",
                params={"language": language},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(
                f"TMDB API error getting season {season_number} metadata for show ID {show_id}: {e}"
            )
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch season {season_number} metadata for show ID {show_id} from TMDB. Error: {e}",
                )
            raise

    def __search_tv(self, query: str, page: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/tv/search",
                params={
                    "query": query,
                    "page": page,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error searching TV shows with query '{query}': {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to search TV shows with query '{query}' on TMDB. Error: {e}",
                )
            raise

    def __get_trending_tv(self) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/tv/trending",
                params={"language": self.default_language},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting trending TV: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch trending TV shows from TMDB. Error: {e}",
                )
            raise

    def __get_movie_metadata(self, movie_id: int, language: str | None = None) -> dict:
        if language is None:
            language = self.default_language
        try:
            response = requests.get(
                url=f"{self.url}/movies/{movie_id}",
                params={"language": language},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting movie metadata for ID {movie_id}: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch movie metadata for ID {movie_id} from TMDB. Error: {e}",
                )
            raise

    def __get_movie_external_ids(self, movie_id: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/movies/{movie_id}/external_ids", timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(
                f"TMDB API error getting movie external IDs for ID {movie_id}: {e}"
            )
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch movie external IDs for ID {movie_id} from TMDB. Error: {e}",
                )
            raise

    def __search_movie(self, query: str, page: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/movies/search",
                params={
                    "query": query,
                    "page": page,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error searching movies with query '{query}': {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to search movies with query '{query}' on TMDB. Error: {e}",
                )
            raise

    def __get_trending_movies(self) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/movies/trending",
                params={"language": self.default_language},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting trending movies: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch trending movies from TMDB. Error: {e}",
                )
            raise

    @override
    def download_show_poster_image(self, show: Show) -> bool:
        # Determine which language to use based on show's original_language
        language = self.__get_language_param(show.original_language)

        # Fetch metadata in the appropriate language to get localized poster
        show_metadata = self.__get_show_metadata(show.external_id, language=language)

        # downloading the poster
        # all pictures from TMDB should already be jpeg, so no need to convert
        if show_metadata["poster_path"] is not None:
            poster_url = (
                "https://image.tmdb.org/t/p/original" + show_metadata["poster_path"]
            )
            if media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path, poster_url=poster_url, uuid=show.id
            ):
                log.info("Successfully downloaded poster image for show " + show.name)
            else:
                log.warning(f"download for image of show {show.name} failed")
                return False
        else:
            log.warning(f"image for show {show.name} could not be downloaded")
            return False
        return True

    @override
    def get_show_metadata(self, show_id: int, language: str | None = None) -> Show:
        """

        :param show_id: the external id of the show
        :type show_id: int
        :param language: optional language code (ISO 639-1) to fetch metadata in
        :type language: str | None
        :return: returns a Show object
        :rtype: Show
        """
        # If language not provided, fetch once to determine original language
        if language is None:
            show_metadata = self.__get_show_metadata(show_id)
            language = show_metadata.get("original_language")

        # Determine which language to use for metadata
        language = self.__get_language_param(language)

        # Fetch show metadata in the appropriate language
        show_metadata = self.__get_show_metadata(show_id, language=language)

        # get imdb id
        external_ids = self.__get_show_external_ids(show_id=show_id)
        imdb_id = external_ids.get("imdb_id")

        season_list = []
        # inserting all the metadata into the objects
        for season in show_metadata["seasons"]:
            season_metadata = self.__get_season_metadata(
                show_id=show_metadata["id"],
                season_number=season["season_number"],
                language=language,
            )
            episode_list = [
                Episode(
                    external_id=int(episode["id"]),
                    title=episode["name"],
                    number=EpisodeNumber(episode["episode_number"]),
                )
                for episode in season_metadata["episodes"]
            ]

            season_list.append(
                Season(
                    external_id=int(season_metadata["id"]),
                    name=season_metadata["name"],
                    overview=season_metadata["overview"],
                    number=SeasonNumber(season_metadata["season_number"]),
                    episodes=episode_list,
                )
            )

        year = media_manager.metadataProvider.utils.get_year_from_date(
            show_metadata["first_air_date"]
        )

        return Show(
            external_id=show_id,
            name=show_metadata["name"],
            overview=show_metadata["overview"],
            year=year,
            seasons=season_list,
            metadata_provider=self.name,
            ended=show_metadata["status"] in ENDED_STATUS,
            original_language=show_metadata.get("original_language"),
            imdb_id=imdb_id,
        )

    @override
    def search_show(
        self, query: str | None = None, max_pages: int = 5
    ) -> list[MetaDataProviderSearchResult]:
        """
        Search for shows using TMDB API.
        If no query is provided, it will return the most popular shows.
        """
        results = []
        if query is None:
            results = self.__get_trending_tv()["results"]
        else:
            for page_number in range(1, max_pages + 1):
                result_page = self.__search_tv(query=query, page=page_number)

                if not result_page["results"]:
                    break
                results.extend(result_page["results"])

        formatted_results = []
        for result in results:
            try:
                if result["poster_path"] is not None:
                    poster_url = (
                        "https://image.tmdb.org/t/p/original" + result["poster_path"]
                    )
                else:
                    poster_url = None

                # Determine which name to use based on primary_languages
                original_language = result.get("original_language")
                original_name = result.get("original_name")
                display_name = result["name"]

                overview = result["overview"]
                # Use original name if language is in primary_languages and skip overview
                if original_language and original_language in self.primary_languages:
                    display_name = original_name
                    overview = None

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_url,
                        overview=overview,
                        name=display_name,
                        external_id=result["id"],
                        year=media_manager.metadataProvider.utils.get_year_from_date(
                            result["first_air_date"]
                        ),
                        metadata_provider=self.name,
                        added=False,
                        vote_average=result["vote_average"],
                        original_language=original_language,
                    )
                )
            except Exception as e:
                log.warning(f"Error processing search result: {e}")
        return formatted_results

    @override
    def get_movie_metadata(self, movie_id: int, language: str | None = None) -> Movie:
        """
        Get movie metadata with language-aware fetching.

        :param movie_id: the external id of the movie
        :type movie_id: int
        :param language: optional language code (ISO 639-1) to fetch metadata in
        :type language: str | None
        :return: returns a Movie object
        :rtype: Movie
        """
        # If language not provided, fetch once to determine original language
        if language is None:
            movie_metadata = self.__get_movie_metadata(movie_id=movie_id)
            language = movie_metadata.get("original_language")

        # Determine which language to use for metadata
        language = self.__get_language_param(language)

        # Fetch movie metadata in the appropriate language
        movie_metadata = self.__get_movie_metadata(movie_id=movie_id, language=language)

        # get imdb id
        external_ids = self.__get_movie_external_ids(movie_id=movie_id)
        imdb_id = external_ids.get("imdb_id")

        year = media_manager.metadataProvider.utils.get_year_from_date(
            movie_metadata["release_date"]
        )

        return Movie(
            external_id=movie_id,
            name=movie_metadata["title"],
            overview=movie_metadata["overview"],
            year=year,
            metadata_provider=self.name,
            original_language=movie_metadata.get("original_language"),
            imdb_id=imdb_id,
        )

    @override
    def search_movie(
        self, query: str | None = None, max_pages: int = 5
    ) -> list[MetaDataProviderSearchResult]:
        """
        Search for movies using TMDB API.
        If no query is provided, it will return the most popular movies.
        """
        results = []
        if query is None:
            results = self.__get_trending_movies()["results"]
        else:
            for page_number in range(1, max_pages + 1):
                result_page = self.__search_movie(query=query, page=page_number)

                if not result_page["results"]:
                    break
                results.extend(result_page["results"])

        formatted_results = []
        for result in results:
            try:
                if result["poster_path"] is not None:
                    poster_url = (
                        "https://image.tmdb.org/t/p/original" + result["poster_path"]
                    )
                else:
                    poster_url = None

                # Determine which name to use based on primary_languages
                original_language = result.get("original_language")
                original_title = result.get("original_title")
                display_name = result["title"]

                overview = result["overview"]
                # Use original name if language is in primary_languages and skip overview
                if original_language and original_language in self.primary_languages:
                    display_name = original_title
                    overview = None

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_url,
                        overview=overview,
                        name=display_name,
                        external_id=result["id"],
                        year=media_manager.metadataProvider.utils.get_year_from_date(
                            result["release_date"]
                        ),
                        metadata_provider=self.name,
                        added=False,
                        vote_average=result["vote_average"],
                        original_language=original_language,
                    )
                )
            except Exception as e:
                log.warning(f"Error processing search result: {e}")
        return formatted_results

    @override
    def download_movie_poster_image(self, movie: Movie) -> bool:
        # Determine which language to use based on movie's original_language
        language = self.__get_language_param(movie.original_language)

        # Fetch metadata in the appropriate language to get localized poster
        movie_metadata = self.__get_movie_metadata(
            movie_id=movie.external_id, language=language
        )

        # downloading the poster
        # all pictures from TMDB should already be jpeg, so no need to convert
        if movie_metadata["poster_path"] is not None:
            poster_url = (
                "https://image.tmdb.org/t/p/original" + movie_metadata["poster_path"]
            )
            if media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path, poster_url=poster_url, uuid=movie.id
            ):
                log.info("Successfully downloaded poster image for movie " + movie.name)
            else:
                log.warning(f"download for image of movie {movie.name} failed")
                return False
        else:
            log.warning(f"image for movie {movie.name} could not be downloaded")
            return False
        return True
