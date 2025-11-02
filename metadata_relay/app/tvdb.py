import os

import tvdb_v4_official
import logging
from fastapi import APIRouter

log = logging.getLogger(__name__)


tvdb_api_key = os.getenv("TVDB_API_KEY")
router = APIRouter(prefix="/tvdb", tags=["TVDB"])

if tvdb_api_key is None:
    log.warning("TVDB_API_KEY environment variable is not set.")
else:
    tvdb_client = tvdb_v4_official.TVDB(tvdb_api_key)

    @router.get("/tv/trending")
    async def get_tvdb_trending_tv():
        return tvdb_client.get_all_series()

    @router.get("/tv/search")
    async def search_tvdb_tv(query: str):
        return tvdb_client.search(query)

    @router.get("/tv/shows/{show_id}")
    async def get_tvdb_show(show_id: int):
        return tvdb_client.get_series_extended(show_id)

    @router.get("/tv/seasons/{season_id}")
    async def get_tvdb_season(season_id: int):
        return tvdb_client.get_season_extended(season_id)

    @router.get("/movies/trending")
    async def get_tvdb_trending_movies():
        return tvdb_client.get_all_movies()

    @router.get("/movies/search")
    async def search_tvdb_movies(query: str):
        return tvdb_client.search(query)

    @router.get("/movies/{movie_id}")
    async def get_tvdb_movie(movie_id: int):
        return tvdb_client.get_movie_extended(movie_id)
