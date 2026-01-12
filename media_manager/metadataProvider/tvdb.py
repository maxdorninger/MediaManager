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
from media_manager.tv.schemas import Episode, Season, SeasonNumber, Show

log = logging.getLogger(__name__)


class TvdbMetadataProvider(AbstractMetadataProvider):
    name = "tvdb"

    def __init__(self) -> None:
        config = MediaManagerConfig().metadata.tvdb
        self.url = config.tvdb_relay_url
        self.primary_languages = config.primary_languages

    def __make_tvdb_request(
        self,
        endpoint: str,
        params: dict | None = None,
        context: str = "TVDB API request",
    ) -> dict:
        """
        Make a TVDB API request with error handling and notifications.

        :param endpoint: API endpoint path (e.g., '/tv/shows/12345')
        :param params: Query parameters
        :param context: Description for error messages
        :return: JSON response as dict
        """
        if params is None:
            params = {}

        try:
            response = requests.get(
                url=f"{self.url}{endpoint}",
                params=params,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TVDB API error for {context}: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TVDB API Error",
                    message=f"Failed to {context}. Error: {e}",
                )
            raise

    def __get_show(self, show_id: int) -> dict:
        return self.__make_tvdb_request(
            endpoint=f"/tv/shows/{show_id}",
            context=f"get show metadata for ID {show_id}",
        )

    def __get_season(self, show_id: int) -> dict:
        return self.__make_tvdb_request(
            endpoint=f"/tv/seasons/{show_id}",
            context=f"get season metadata for ID {show_id}",
        )

    def __search_tv(self, query: str) -> dict:
        return self.__make_tvdb_request(
            endpoint="/tv/search",
            params={"query": query},
            context=f"search TV shows with query '{query}'",
        )

    def __get_trending_tv(self) -> dict:
        return self.__make_tvdb_request(
            endpoint="/tv/trending",
            context="get trending TV shows",
        )

    def __get_movie(self, movie_id: int) -> dict:
        return self.__make_tvdb_request(
            endpoint=f"/movies/{movie_id}",
            context=f"get movie metadata for ID {movie_id}",
        )

    def __search_movie(self, query: str) -> dict:
        return self.__make_tvdb_request(
            endpoint="/movies/search",
            params={"query": query},
            context=f"search movies with query '{query}'",
        )

    def __get_trending_movies(self) -> dict:
        return self.__make_tvdb_request(
            endpoint="/movies/trending",
            context="get trending movies",
        )

    @override
    def download_show_poster_image(self, show: Show) -> bool:
        show_metadata = self.__get_show(show_id=show.external_id)

        if show_metadata["image"] is not None:
            media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path,
                poster_url=show_metadata["image"],
                uuid=show.id,
            )
            log.info("Successfully downloaded poster image for show " + show.name)
            return True
        log.warning(f"image for show {show.name} could not be downloaded")
        return False

    @override
    def get_show_metadata(
        self, show_id: int, original_language: str | None = None
    ) -> Show:
        """
        Get show metadata with language-aware fetching.

        :param show_id: The external id of the show
        :type show_id: int
        :param original_language: optional original language code (ISO 639-1) to fetch metadata in
        :type original_language: str | None
        :return: returns a Show object
        :rtype: Show
        """
        series = self.__get_show(show_id)
        
        # Extract original language from the response if not provided
        if original_language is None:
            original_language = series.get("original_language")
        
        seasons = []
        seasons_ids = [season["id"] for season in series["seasons"]]

        # get imdb id from remote ids
        imdb_id = None
        remote_ids = series.get("remoteIds", None)
        if remote_ids:
            for remote_id in remote_ids:
                if remote_id.get("type") == 2:
                    imdb_id = remote_id.get("id")

        for season in seasons_ids:
            s = self.__get_season(show_id=season)
            # the seasons need to be filtered to a certain type,
            # otherwise the same season will be imported in aired and dvd order,
            # which causes duplicate season number + show ids which in turn violates a unique constraint of the season table
            if s["type"]["id"] != 1:
                log.info(
                    f"Season {s['type']['id']} will not be downloaded because it is not a 'aired order' season"
                )
                continue

            episodes = [
                Episode(
                    number=episode["number"],
                    external_id=episode["id"],
                    title=episode["name"],
                )
                for episode in s["episodes"]
            ]
            seasons.append(
                Season(
                    number=SeasonNumber(s["number"]),
                    name="TVDB doesn't provide Season Names",
                    overview="TVDB doesn't provide Season Overviews",
                    external_id=int(s["id"]),
                    episodes=episodes,
                )
            )

        return Show(
            name=series["name"],
            overview=series["overview"],
            year=series.get("year"),
            external_id=series["id"],
            metadata_provider=self.name,
            seasons=seasons,
            ended=False,
            original_language=original_language,
            imdb_id=imdb_id,
        )

    @override
    def search_show(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        if query:
            results = self.__search_tv(query=query)
            formatted_results = []
            for result in results:
                try:
                    if result["type"] == "series":
                        try:
                            year = result["year"]
                        except KeyError:
                            year = None

                        formatted_results.append(
                            MetaDataProviderSearchResult(
                                poster_path=result.get("image_url"),
                                overview=result.get("overview"),
                                name=result["name"],
                                external_id=result["tvdb_id"],
                                year=year,
                                metadata_provider=self.name,
                                added=False,
                                vote_average=None,
                                original_language=result.get("primary_language"),
                            )
                        )
                except Exception as e:
                    log.warning(f"Error processing search result: {e}")
            return formatted_results
        results = self.__get_trending_tv()
        formatted_results = []
        for result in results:
            try:
                if result["type"] == "series":
                    try:
                        year = result["year"]
                    except KeyError:
                        year = None

                    formatted_results.append(
                        MetaDataProviderSearchResult(
                            poster_path="https://artworks.thetvdb.com"
                            + result.get("image")
                            if result.get("image")
                            else None,
                            overview=result.get("overview"),
                            name=result["name"],
                            external_id=result["id"],
                            year=year,
                            metadata_provider=self.name,
                            added=False,
                            vote_average=None,
                            original_language=result.get("primary_language"),
                        )
                    )
            except Exception as e:
                log.warning(f"Error processing search result: {e}")
        return formatted_results

    @override
    def search_movie(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        if query:
            results = self.__search_movie(query=query)
            results = results[0:20]
            log.debug(f"got {len(results)} results from TVDB search")
            formatted_results = []
            for result in results:
                try:
                    if result["type"] != "movie":
                        continue

                    try:
                        year = result["year"]
                    except KeyError:
                        year = None

                    formatted_results.append(
                        MetaDataProviderSearchResult(
                            poster_path=result.get("image_url"),
                            overview=result.get("overview"),
                            name=result["name"],
                            external_id=result["tvdb_id"],
                            year=year,
                            metadata_provider=self.name,
                            added=False,
                            vote_average=None,
                            original_language=result.get("primary_language"),
                        )
                    )
                except Exception as e:
                    log.warning(f"Error processing search result: {e}")
            return formatted_results
        results = self.__get_trending_movies()
        results = results[0:20]
        log.debug(f"got {len(results)} results from TVDB search")
        formatted_results = []
        for result in results:
            try:
                try:
                    year = result["year"]
                except KeyError:
                    year = None

                if result.get("image"):
                    poster_path = "https://artworks.thetvdb.com" + str(result.get("image"))
                else:
                    poster_path = None

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_path,
                        overview=result.get("overview"),
                        name=result["name"],
                        external_id=result["id"],
                        year=year,
                        metadata_provider=self.name,
                        added=False,
                        vote_average=None,
                        original_language=result.get("primary_language"),
                    )
                )
            except Exception as e:
                log.warning(f"Error processing search result: {e}")
        return formatted_results

    @override
    def download_movie_poster_image(self, movie: Movie) -> bool:
        movie_metadata = self.__get_movie(movie.external_id)

        if movie_metadata["image"] is not None:
            media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path,
                poster_url=movie_metadata["image"],
                uuid=movie.id,
            )
            log.info("Successfully downloaded poster image for movie " + movie.name)
            return True
        log.warning(f"image for movie {movie.name} could not be downloaded")
        return False

    @override
    def get_movie_metadata(
        self, movie_id: int, original_language: str | None = None
    ) -> Movie:
        """
        Get movie metadata with language support.

        :param movie_id: the external id of the movie
        :type movie_id: int
        :param original_language: optional original language code (ISO 639-1)
        :type original_language: str | None
        :return: returns a Movie object
        """
        movie = self.__get_movie(movie_id=movie_id)

        # Extract original language from the response if not provided
        if original_language is None:
            original_language = movie.get("original_language")

        # get imdb id from remote ids
        imdb_id = None
        remote_ids = movie.get("remoteIds", None)
        if remote_ids:
            for remote_id in remote_ids:
                if remote_id.get("type") == 2:
                    imdb_id = remote_id.get("id")

        return Movie(
            name=movie["name"],
            overview=movie.get("overview", "No overview available"),
            year=movie.get("year"),
            external_id=movie["id"],
            metadata_provider=self.name,
            imdb_id=imdb_id,
            original_language=original_language,
        )
