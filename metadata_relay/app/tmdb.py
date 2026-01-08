import logging
import os

import tmdbsimple
from fastapi import APIRouter
from tmdbsimple import TV, Movies, Search, Trending, TV_Seasons

log = logging.getLogger(__name__)

tmdb_api_key = os.getenv("TMDB_API_KEY")
router = APIRouter(prefix="/tmdb", tags=["TMDB"])

if tmdb_api_key is None:
    log.warning("TMDB_API_KEY environment variable is not set.")
else:
    tmdbsimple.API_KEY = tmdb_api_key

    @router.get("/tv/trending")
    async def get_tmdb_trending_tv(language: str = "en") -> dict:
        return Trending(media_type="tv").info(language=language)

    @router.get("/tv/search")
    async def search_tmdb_tv(query: str, page: int = 1, language: str = "en") -> dict:
        return Search().tv(page=page, query=query, language=language)

    @router.get("/tv/shows/{show_id}")
    async def get_tmdb_show(show_id: int, language: str = "en") -> dict:
        return TV(show_id).info(language=language)

    @router.get("/tv/shows/{show_id}/external_ids")
    async def get_tmdb_show_external_ids(show_id: int) -> dict:
        return TV(show_id).external_ids()

    @router.get("/tv/shows/{show_id}/{season_number}")
    async def get_tmdb_season(
        season_number: int, show_id: int, language: str = "en"
    ) -> dict:
        return TV_Seasons(season_number=season_number, tv_id=show_id).info(
            language=language
        )

    @router.get("/movies/trending")
    async def get_tmdb_trending_movies(language: str = "en") -> dict:
        return Trending(media_type="movie").info(language=language)

    @router.get("/movies/search")
    async def search_tmdb_movies(
        query: str, page: int = 1, language: str = "en"
    ) -> dict:
        return Search().movie(page=page, query=query, language=language)

    @router.get("/movies/{movie_id}")
    async def get_tmdb_movie(movie_id: int, language: str = "en") -> dict:
        return Movies(movie_id).info(language=language)

    @router.get("/movies/{movie_id}/external_ids")
    async def get_tmdb_movie_external_ids(movie_id: int) -> dict:
        return Movies(movie_id).external_ids()
