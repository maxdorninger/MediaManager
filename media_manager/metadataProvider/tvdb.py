import requests
import logging


import media_manager.metadataProvider.utils
from media_manager.config import AllEncompassingConfig
from media_manager.metadataProvider.abstractMetaDataProvider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.torrent.utils import remove_special_chars_and_parentheses
from media_manager.tv.schemas import Episode, Season, Show, SeasonNumber
from media_manager.movies.schemas import Movie


log = logging.getLogger(__name__)


class TvdbMetadataProvider(AbstractMetadataProvider):
    name = "tvdb"

    def __init__(self):
        config = AllEncompassingConfig().metadata.tvdb
        self.url = config.tvdb_relay_url

    def __get_show(self, id: int) -> dict:
        return requests.get(f"{self.url}/tv/shows/{id}").json()

    def __get_season(self, id: int) -> dict:
        return requests.get(f"{self.url}/tv/seasons/{id}").json()

    def __search_tv(self, query: str) -> dict:
        return requests.get(
            f"{self.url}/tv/search",
            params={"query": remove_special_chars_and_parentheses(query)},
        ).json()

    def __get_trending_tv(self) -> dict:
        return requests.get(f"{self.url}/tv/trending").json()

    def __get_movie(self, id: int) -> dict:
        return requests.get(f"{self.url}/movies/{id}").json()

    def __search_movie(self, query: str) -> dict:
        return requests.get(
            f"{self.url}/movies/search",
            params={"query": remove_special_chars_and_parentheses(query)},
        ).json()

    def __get_trending_movies(self) -> dict:
        return requests.get(f"{self.url}/movies/trending").json()

    def download_show_poster_image(self, show: Show) -> bool:
        show_metadata = self.__get_show(id=show.external_id)

        if show_metadata["image"] is not None:
            media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path,
                poster_url=show_metadata["image"],
                id=show.id,
            )
            log.debug("Successfully downloaded poster image for show " + show.name)
            return True
        else:
            log.warning(f"image for show {show.name} could not be downloaded")
            return False

    def get_show_metadata(self, id: int = None) -> Show:
        """

        :param id: the external id of the show
        :type id: int
        :return: returns a ShowMetadata object
        :rtype: ShowMetadata
        """
        series = self.__get_show(id=id)
        seasons = []
        seasons_ids = [season["id"] for season in series["seasons"]]

        for season in seasons_ids:
            s = self.__get_season(id=season)
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
        try:
            year = series["year"]
        except KeyError:
            year = None
        # NOTE: the TVDB API is fucking shit and seems to be very poorly documentated, I can't for the life of me
        #  figure out which statuses this fucking api returns
        show = Show(
            name=series["name"],
            overview=series["overview"],
            year=year,
            external_id=series["id"],
            metadata_provider=self.name,
            seasons=seasons,
            ended=False,
        )

        return show

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
                                poster_path=result["image_url"],
                                overview=result["overview"],
                                name=result["name"],
                                external_id=result["tvdb_id"],
                                year=year,
                                metadata_provider=self.name,
                                added=False,
                                vote_average=None,
                            )
                        )
                except Exception as e:
                    log.warning(f"Error processing search result: {e}")
            return formatted_results
        else:
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
                                poster_path=result["image"],
                                overview=result["overview"],
                                name=result["name"],
                                external_id=result["id"],
                                year=year,
                                metadata_provider=self.name,
                                added=False,
                                vote_average=None,
                            )
                        )
                except Exception as e:
                    log.warning(f"Error processing search result: {e}")
            return formatted_results

    def search_movie(
        self, query: str | None = None
    ) -> list[MetaDataProviderSearchResult]:
        if query is None:
            results = self.__get_trending_movies()
            results = results[0:20]
            log.debug(f"got {len(results)} results from TVDB search")
            formatted_results = []
            for result in results:
                result = self.__get_movie(result["id"])
                try:
                    try:
                        year = result["year"]
                    except KeyError:
                        year = None

                    formatted_results.append(
                        MetaDataProviderSearchResult(
                            poster_path=result["image"],
                            overview="TVDB does not provide overviews",
                            name=result["name"],
                            external_id=result["id"],
                            year=year,
                            metadata_provider=self.name,
                            added=False,
                            vote_average=None,
                        )
                    )
                except Exception as e:
                    log.warning(f"Error processing search result: {e}")
            return formatted_results
        else:
            results = self.__search_movie(query=query)
            results = results[0:20]
            log.debug(f"got {len(results)} results from TVDB search")
            formatted_results = []
            for result in results:
                if result["type"] != "movie":
                    continue

                result = self.__get_movie(result["tvdb_id"])

                try:
                    try:
                        year = result["year"]
                    except KeyError:
                        year = None

                    formatted_results.append(
                        MetaDataProviderSearchResult(
                            poster_path=result["image_url"],
                            overview="TVDB does not provide overviews",
                            name=result["name"],
                            external_id=result["tvdb_id"],
                            year=year,
                            metadata_provider=self.name,
                            added=False,
                            vote_average=None,
                        )
                    )
                except Exception as e:
                    log.warning(f"Error processing search result: {e}")
            return formatted_results

    def download_movie_poster_image(self, movie: Movie) -> bool:
        movie_metadata = self.__get_movie(movie.external_id)

        if movie_metadata["image"] is not None:
            media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path,
                poster_url=movie_metadata["image"],
                id=movie.id,
            )
            log.info("Successfully downloaded poster image for show " + movie.name)
            return True
        else:
            log.warning(f"image for show {movie.name} could not be downloaded")
            return False

    def get_movie_metadata(self, id: int = None) -> Movie:
        """

        :param id: the external id of the movie
        :type id: int
        :return: returns a Movie object
        :rtype: Movie
        """
        movie = self.__get_movie(id)
        try:
            year = movie["year"]
        except KeyError:
            year = None

        movie = Movie(
            name=movie["name"],
            overview="TVDB does not provide overviews",
            year=year,
            external_id=movie["id"],
            metadata_provider=self.name,
        )

        return movie
