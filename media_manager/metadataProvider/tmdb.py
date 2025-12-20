import logging

import requests

import media_manager.metadataProvider.utils
from media_manager.config import AllEncompassingConfig
from media_manager.metadataProvider.abstractMetaDataProvider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.tv.schemas import Episode, Season, Show, SeasonNumber, EpisodeNumber
from media_manager.movies.schemas import Movie
from media_manager.notification.manager import notification_manager


ENDED_STATUS = {"Ended", "Canceled"}

log = logging.getLogger(__name__)


class TmdbMetadataProvider(AbstractMetadataProvider):
    name = "tmdb"

    def __init__(self):
        config = AllEncompassingConfig().metadata.tmdb
        self.url = config.tmdb_relay_url

    def __get_show_metadata(self, id: int) -> dict:
        try:
            response = requests.get(url=f"{self.url}/tv/shows/{id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting show metadata for ID {id}: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch show metadata for ID {id} from TMDB. Error: {str(e)}",
                )
            raise

    def __get_season_metadata(self, show_id: int, season_number: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/tv/shows/{show_id}/{season_number}"
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
                    message=f"Failed to fetch season {season_number} metadata for show ID {show_id} from TMDB. Error: {str(e)}",
                )
            raise

    def __search_tv(self, query: str, page: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/tv/search", params={"query": query, "page": page}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error searching TV shows with query '{query}': {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to search TV shows with query '{query}' on TMDB. Error: {str(e)}",
                )
            raise

    def __get_trending_tv(self) -> dict:
        try:
            response = requests.get(url=f"{self.url}/tv/trending")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting trending TV: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch trending TV shows from TMDB. Error: {str(e)}",
                )
            raise

    def __get_movie_metadata(self, id: int) -> dict:
        try:
            response = requests.get(url=f"{self.url}/movies/{id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting movie metadata for ID {id}: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch movie metadata for ID {id} from TMDB. Error: {str(e)}",
                )
            raise

    def __search_movie(self, query: str, page: int) -> dict:
        try:
            response = requests.get(
                url=f"{self.url}/movies/search", params={"query": query, "page": page}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error searching movies with query '{query}': {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to search movies with query '{query}' on TMDB. Error: {str(e)}",
                )
            raise

    def __get_trending_movies(self) -> dict:
        try:
            response = requests.get(url=f"{self.url}/movies/trending")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            log.error(f"TMDB API error getting trending movies: {e}")
            if notification_manager.is_configured():
                notification_manager.send_notification(
                    title="TMDB API Error",
                    message=f"Failed to fetch trending movies from TMDB. Error: {str(e)}",
                )
            raise

    def download_show_poster_image(self, show: Show) -> bool:
        show_metadata = self.__get_show_metadata(show.external_id)
        # downloading the poster
        # all pictures from TMDB should already be jpeg, so no need to convert
        if show_metadata["poster_path"] is not None:
            poster_url = (
                "https://image.tmdb.org/t/p/original" + show_metadata["poster_path"]
            )
            if media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path, poster_url=poster_url, id=show.id
            ):
                log.info("Successfully downloaded poster image for show " + show.name)
            else:
                log.warning(f"download for image of show {show.name} failed")
                return False
        else:
            log.warning(f"image for show {show.name} could not be downloaded")
            return False
        return True

    def get_show_metadata(self, id: int = None) -> Show:
        """

        :param id: the external id of the show
        :type id: int
        :return: returns a ShowMetadata object
        :rtype: ShowMetadata
        """
        show_metadata = self.__get_show_metadata(id)
        season_list = []
        # inserting all the metadata into the objects
        for season in show_metadata["seasons"]:
            season_metadata = self.__get_season_metadata(
                show_id=show_metadata["id"], season_number=season["season_number"]
            )
            episode_list = []

            for episode in season_metadata["episodes"]:
                episode_list.append(
                    Episode(
                        external_id=int(episode["id"]),
                        title=episode["name"],
                        number=EpisodeNumber(episode["episode_number"]),
                    )
                )

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

        show = Show(
            external_id=id,
            name=show_metadata["name"],
            overview=show_metadata["overview"],
            year=year,
            seasons=season_list,
            metadata_provider=self.name,
            ended=show_metadata["status"] in ENDED_STATUS,
            imdb_id=show_metadata.get("imdb_id")
        )

        return show

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
                else:
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
                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_url,
                        overview=result["overview"],
                        name=result["name"],
                        external_id=result["id"],
                        year=media_manager.metadataProvider.utils.get_year_from_date(
                            result["first_air_date"]
                        ),
                        metadata_provider=self.name,
                        added=False,
                        vote_average=result["vote_average"],
                    )
                )
            except Exception as e:
                log.warning(f"Error processing search result: {e}")
        return formatted_results

    def get_movie_metadata(self, id: int = None) -> Movie:
        """

        :param id: the external id of the show
        :type id: int
        :return: returns a ShowMetadata object
        :rtype: ShowMetadata
        """
        movie_metadata = self.__get_movie_metadata(id=id)
        year = media_manager.metadataProvider.utils.get_year_from_date(
            movie_metadata["release_date"]
        )

        movie = Movie(
            external_id=id,
            name=movie_metadata["title"],
            overview=movie_metadata["overview"],
            year=year,
            metadata_provider=self.name,
            imdb_id=movie_metadata.get("imdb_id"),
        )

        return movie

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
                else:
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
                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_url,
                        overview=result["overview"],
                        name=result["title"],
                        external_id=result["id"],
                        year=media_manager.metadataProvider.utils.get_year_from_date(
                            result["release_date"]
                        ),
                        metadata_provider=self.name,
                        added=False,
                        vote_average=result["vote_average"],
                    )
                )
            except Exception as e:
                log.warning(f"Error processing search result: {e}")
        return formatted_results

    def download_movie_poster_image(self, movie: Movie) -> bool:
        movie_metadata = self.__get_movie_metadata(id=movie.external_id)
        # downloading the poster
        # all pictures from TMDB should already be jpeg, so no need to convert
        if movie_metadata["poster_path"] is not None:
            poster_url = (
                "https://image.tmdb.org/t/p/original" + movie_metadata["poster_path"]
            )
            if media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path, poster_url=poster_url, id=movie.id
            ):
                log.info("Successfully downloaded poster image for show " + movie.name)
            else:
                log.warning(f"download for image of show {movie.name} failed")
                return False
        else:
            log.warning(f"image for show {movie.name} could not be downloaded")
            return False
        return True
