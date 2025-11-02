import logging
import os

import tmdbsimple
from tmdbsimple import TV, TV_Seasons, Movies, Trending, Search
from fastapi import APIRouter

log = logging.getLogger(__name__)

tmdb_api_key = os.getenv("TMDB_API_KEY")
router = APIRouter(prefix="/tmdb", tags=["TMDB"])

if tmdb_api_key is None:
    log.warning("TMDB_API_KEY environment variable is not set.")
else:
    tmdbsimple.API_KEY = tmdb_api_key

    @router.get("/tv/trending")
    async def get_tmdb_trending_tv():
        return Trending(media_type="tv").info()

    @router.get("/tv/search")
    async def search_tmdb_tv(query: str, page: int = 1):
        return Search().tv(page=page, query=query, include_adult=True)

    @router.get("/tv/shows/{show_id}")
    async def get_tmdb_show(show_id: int):
        return TV(show_id).info()

    @router.get("/tv/shows/{show_id}/{season_number}")
    async def get_tmdb_season(season_number: int, show_id: int):
        return TV_Seasons(season_number=season_number, tv_id=show_id).info()

    @router.get("/movies/trending")
    async def get_tmdb_trending_movies():
        return Trending(media_type="movie").info()

    @router.get("/movies/search")
    async def search_tmdb_movies(query: str, page: int = 1):
        return Search().movie(page=page, query=query, include_adult=True)

    @router.get("/movies/{movie_id}")
    async def get_tmdb_movie(movie_id: int):
        return Movies(movie_id).info()
