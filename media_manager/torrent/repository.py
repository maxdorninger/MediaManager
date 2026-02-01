from sqlalchemy import delete, select

from media_manager.database import DbSessionDependency
from media_manager.exceptions import NotFoundError
from media_manager.movies.models import Movie, MovieFile
from media_manager.movies.schemas import (
    Movie as MovieSchema,
)
from media_manager.movies.schemas import (
    MovieFile as MovieFileSchema,
)
from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import Torrent as TorrentSchema
from media_manager.torrent.schemas import TorrentId
from media_manager.tv.models import Season, SeasonFile, Show
from media_manager.tv.schemas import SeasonFile as SeasonFileSchema
from media_manager.tv.schemas import Show as ShowSchema


class TorrentRepository:
    def __init__(self, db: DbSessionDependency) -> None:
        self.db = db

    def get_seasons_files_of_torrent(
        self, torrent_id: TorrentId
    ) -> list[SeasonFileSchema]:
        stmt = select(SeasonFile).where(SeasonFile.torrent_id == torrent_id)
        result = self.db.execute(stmt).scalars().all()
        return [SeasonFileSchema.model_validate(season_file) for season_file in result]

    def get_show_of_torrent(self, torrent_id: TorrentId) -> ShowSchema | None:
        stmt = (
            select(Show)
            .join(SeasonFile.season)
            .join(Season.show)
            .where(SeasonFile.torrent_id == torrent_id)
        )
        result = self.db.execute(stmt).unique().scalar_one_or_none()
        if result is None:
            return None
        return ShowSchema.model_validate(result)

    def save_torrent(self, torrent: TorrentSchema) -> TorrentSchema:
        self.db.merge(Torrent(**torrent.model_dump()))
        self.db.commit()
        return TorrentSchema.model_validate(torrent)

    def get_all_torrents(self) -> list[TorrentSchema]:
        stmt = select(Torrent)
        result = self.db.execute(stmt).scalars().all()

        return [
            TorrentSchema.model_validate(torrent_schema) for torrent_schema in result
        ]

    def get_torrent_by_id(self, torrent_id: TorrentId) -> TorrentSchema:
        result = self.db.get(Torrent, torrent_id)
        if result is None:
            msg = f"Torrent with ID {torrent_id} not found."
            raise NotFoundError(msg)
        return TorrentSchema.model_validate(result)

    def delete_torrent(
        self, torrent_id: TorrentId, delete_associated_media_files: bool = False
    ) -> None:
        if delete_associated_media_files:
            movie_files_stmt = delete(MovieFile).where(
                MovieFile.torrent_id == torrent_id
            )
            self.db.execute(movie_files_stmt)

            season_files_stmt = delete(SeasonFile).where(
                SeasonFile.torrent_id == torrent_id
            )
            self.db.execute(season_files_stmt)

        self.db.delete(self.db.get(Torrent, torrent_id))

    def get_movie_of_torrent(self, torrent_id: TorrentId) -> MovieSchema | None:
        stmt = (
            select(Movie)
            .join(MovieFile, Movie.id == MovieFile.movie_id)
            .where(MovieFile.torrent_id == torrent_id)
        )
        result = self.db.execute(stmt).unique().scalar_one_or_none()
        if result is None:
            return None
        return MovieSchema.model_validate(result)

    def get_movie_files_of_torrent(
        self, torrent_id: TorrentId
    ) -> list[MovieFileSchema]:
        stmt = select(MovieFile).where(MovieFile.torrent_id == torrent_id)
        result = self.db.execute(stmt).scalars().all()
        return [MovieFileSchema.model_validate(movie_file) for movie_file in result]
