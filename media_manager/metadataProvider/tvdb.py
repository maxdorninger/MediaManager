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
from media_manager.tv.schemas import Episode, Season, SeasonNumber, Show

log = logging.getLogger(__name__)


class TvdbMetadataProvider(AbstractMetadataProvider):
    name = "tvdb"

    def __init__(self) -> None:
        config = MediaManagerConfig().metadata.tvdb
        self.url = config.tvdb_relay_url

    def __get_show(self, show_id: int) -> dict:
        return requests.get(url=f"{self.url}/tv/shows/{show_id}", timeout=60).json()

    def __get_season(self, show_id: int) -> dict:
        return requests.get(url=f"{self.url}/tv/seasons/{show_id}", timeout=60).json()

    def __search_tv(self, query: str) -> dict:
        return requests.get(
            url=f"{self.url}/tv/search", params={"query": query}, timeout=60
        ).json()

    def __get_trending_tv(self) -> dict:
        return requests.get(url=f"{self.url}/tv/trending", timeout=60).json()

    def __get_movie(self, movie_id: int) -> dict:
        return requests.get(url=f"{self.url}/movies/{movie_id}", timeout=60).json()

    def __search_movie(self, query: str) -> dict:
        return requests.get(
            url=f"{self.url}/movies/search", params={"query": query}, timeout=60
        ).json()

    def __get_trending_movies(self) -> dict:
        return requests.get(url=f"{self.url}/movies/trending", timeout=60).json()

    @override
    def download_show_poster_image(self, show: Show) -> bool:
        show_metadata = self.__get_show(show_id=show.external_id)

        if show_metadata["image"] is not None:
            media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path,
                poster_url=show_metadata["image"],
                uuid=show.id,
            )
            log.debug("Successfully downloaded poster image for show " + show.name)
            return True
        log.warning(f"image for show {show.name} could not be downloaded")
        return False

    @override
    def get_show_metadata(self, show_id: int, language: str | None = None) -> Show:
        """

        :param show_id: The external id of the show
        :param language: does nothing, TVDB does not support multiple languages
        """
        series = self.__get_show(show_id)
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
                            poster_path=result.get("image_url"),
                            overview=result.get("overview"),
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

                if result.get("image"):
                    poster_path = "https://artworks.thetvdb.com" + str(
                        result.get("image")
                    )
                else:
                    poster_path = None

                formatted_results.append(
                    MetaDataProviderSearchResult(
                        poster_path=poster_path if result.get("image") else None,
                        overview=result.get("overview"),
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

    @override
    def download_movie_poster_image(self, movie: Movie) -> bool:
        movie_metadata = self.__get_movie(movie.external_id)

        if movie_metadata["image"] is not None:
            media_manager.metadataProvider.utils.download_poster_image(
                storage_path=self.storage_path,
                poster_url=movie_metadata["image"],
                uuid=movie.id,
            )
            log.info("Successfully downloaded poster image for show " + movie.name)
            return True
        log.warning(f"image for show {movie.name} could not be downloaded")
        return False

    @override
    def get_movie_metadata(self, movie_id: int, language: str | None = None) -> Movie:
        """

        :param movie_id: the external id of the movie
        :param language: does nothing, TVDB does not support multiple languages
        :return: returns a Movie object
        """
        movie = self.__get_movie(movie_id=movie_id)

        # get imdb id from remote ids
        imdb_id = None
        remote_ids = movie.get("remoteIds", None)
        if remote_ids:
            for remote_id in remote_ids:
                if remote_id.get("type") == 2:
                    imdb_id = remote_id.get("id")

        return Movie(
            name=movie["name"],
            overview="Overviews are not supported with TVDB",
            year=movie.get("year"),
            external_id=movie["id"],
            metadata_provider=self.name,
            imdb_id=imdb_id,
        )
