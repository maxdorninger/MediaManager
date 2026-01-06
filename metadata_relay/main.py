import os

from app.tmdb import router as tmdb_router
from app.tvdb import router as tvdb_router
from fastapi import FastAPI
from starlette_exporter import PrometheusMiddleware, handle_metrics

app = FastAPI(root_path=os.getenv("BASE_PATH"))

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

app.include_router(tmdb_router)
app.include_router(tvdb_router)


@app.get("/")
async def root() -> dict:
    return {"message": "Hello World"}
