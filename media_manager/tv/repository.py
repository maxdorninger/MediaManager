from sqlalchemy import distinct, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from media_manager.common.repository import BaseRepository
from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.torrent.models import Torrent as TorrentModel
from media_manager.torrent.schemas import Torrent as TorrentSchema
from media_manager.torrent.schemas import TorrentId
from media_manager.tv import log
from media_manager.tv.models import Episode, EpisodeFile, Season, Show
from media_manager.tv.schemas import Episode as EpisodeSchema
from media_manager.tv.schemas import EpisodeFile as EpisodeFileSchema
from media_manager.tv.schemas import (
    EpisodeId,
    EpisodeNumber,
    SeasonId,
    SeasonNumber,
    ShowId,
)
from media_manager.tv.schemas import Season as SeasonSchema
from media_manager.tv.schemas import Show as ShowSchema


class TvRepository(BaseRepository[Show, ShowSchema]):
    """
    Repository for managing TV shows, seasons, and episodes in the database.
    Provides methods to retrieve, save, and delete shows and seasons.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, Show, ShowSchema)

    def get_show_by_id(self, show_id: ShowId) -> ShowSchema:
        try:
            stmt = (
                select(Show)
                .where(Show.id == show_id)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Show with id {show_id} not found."
                raise NotFoundError(msg)
        except SQLAlchemyError:
            log.exception(f"Database error while retrieving show {show_id}")
            raise
        else:
            return ShowSchema.model_validate(result)

    def get_show_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> ShowSchema:
        try:
            stmt = (
                select(Show)
                .where(Show.external_id == external_id)
                .where(Show.metadata_provider == metadata_provider)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Show with external_id {external_id} and provider {metadata_provider} not found."
                raise NotFoundError(msg)
        except SQLAlchemyError:
            log.exception(
                f"Database error while retrieving show by external_id {external_id}",
            )
            raise
        else:
            return ShowSchema.model_validate(result)

    def get_shows(self) -> list[ShowSchema]:
        try:
            stmt = select(Show).options(
                joinedload(Show.seasons).joinedload(Season.episodes)
            )
            results = self.db.execute(stmt).scalars().unique().all()
        except SQLAlchemyError:
            log.exception("Database error while retrieving all shows")
            raise
        else:
            return [ShowSchema.model_validate(show) for show in results]

    delete_show = BaseRepository.delete
    set_show_library = BaseRepository.set_library

    def get_total_downloaded_episodes_count(self) -> int:
        try:
            stmt = (
                select(func.count(distinct(Episode.id)))
                .select_from(Episode)
                .join(EpisodeFile)
            )
            result = self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            log.exception("Database error while calculating downloaded episodes count")
            raise
        else:
            return result or 0

    def save_show(self, show: ShowSchema) -> ShowSchema:
        db_show = self.db.get(Show, show.id) if show.id else None

        if db_show:  # Use base for update
            return self.save_media_base(
                media_schema=show, model_class=Show, exclude={"seasons", "episodes"}
            )

        # Custom insertion for nested seasons/episodes
        db_show = Show(
            id=show.id,
            external_id=show.external_id,
            metadata_provider=show.metadata_provider,
            name=show.name,
            overview=show.overview,
            year=show.year,
            ended=show.ended,
            original_language=show.original_language,
            imdb_id=show.imdb_id,
            continuous_download=show.continuous_download,
            library=show.library,
            seasons=[
                Season(
                    id=season.id,
                    show_id=show.id,
                    number=season.number,
                    external_id=season.external_id,
                    name=season.name,
                    overview=season.overview,
                    episodes=[
                        Episode(
                            id=episode.id,
                            season_id=season.id,
                            number=episode.number,
                            external_id=episode.external_id,
                            title=episode.title,
                            overview=episode.overview,
                        )
                        for episode in season.episodes
                    ],
                )
                for season in show.seasons
            ],
        )
        self.db.add(db_show)
        try:
            self.db.commit()
            self.db.refresh(db_show)
        except IntegrityError as e:
            self.db.rollback()
            msg = f"Integrity error: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            raise
        else:
            return ShowSchema.model_validate(db_show)

    def get_season(self, season_id: SeasonId) -> SeasonSchema:
        season = self.db.get(Season, season_id)
        if not season:
            msg = f"Season {season_id} not found"
            raise NotFoundError(msg)
        return SeasonSchema.model_validate(season)

    def get_episode(self, episode_id: EpisodeId) -> EpisodeSchema:
        episode = self.db.get(Episode, episode_id)
        if not episode:
            msg = f"Episode {episode_id} not found"
            raise NotFoundError(msg)
        return EpisodeSchema.model_validate(episode)

    def get_season_by_episode(self, episode_id: EpisodeId) -> SeasonSchema:
        stmt = select(Season).join(Season.episodes).where(Episode.id == episode_id)
        season = self.db.scalar(stmt)
        if not season:
            msg = f"Season for episode {episode_id} not found"
            raise NotFoundError(msg)
        return SeasonSchema.model_validate(season)

    def get_season_by_number(self, season_number: int, show_id: ShowId) -> SeasonSchema:
        stmt = (
            select(Season)
            .where(Season.show_id == show_id)
            .where(Season.number == season_number)
            .options(joinedload(Season.episodes), joinedload(Season.show))
        )
        result = self.db.execute(stmt).unique().scalar_one_or_none()
        if not result:
            msg = f"Season {season_number} for show {show_id} not found"
            raise NotFoundError(msg)
        return SeasonSchema.model_validate(result)

    def add_episode_file(self, episode_file: EpisodeFileSchema) -> EpisodeFileSchema:
        return self.add_media_file_base(
            file_schema=episode_file,
            model_class=EpisodeFile,
            schema_class=EpisodeFileSchema,
        )

    def remove_episode_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        return self.remove_files_by_torrent_id_base(
            torrent_id=torrent_id, model_class=EpisodeFile
        )

    def get_episode_files_by_season_id(
        self, season_id: SeasonId
    ) -> list[EpisodeFileSchema]:
        stmt = select(EpisodeFile).join(Episode).where(Episode.season_id == season_id)
        results = self.db.execute(stmt).scalars().all()
        return [EpisodeFileSchema.model_validate(ef) for ef in results]

    def get_episode_files_by_episode_id(
        self, episode_id: EpisodeId
    ) -> list[EpisodeFileSchema]:
        stmt = select(EpisodeFile).where(EpisodeFile.episode_id == episode_id)
        results = self.db.execute(stmt).scalars().all()
        return [EpisodeFileSchema.model_validate(sf) for sf in results]

    def get_torrents_by_show_id(self, show_id: ShowId) -> list[TorrentSchema]:
        stmt = (
            select(TorrentModel)
            .distinct()
            .join(EpisodeFile, EpisodeFile.torrent_id == TorrentModel.id)
            .join(Episode, Episode.id == EpisodeFile.episode_id)
            .join(Season, Season.id == Episode.season_id)
            .where(Season.show_id == show_id)
        )
        results = self.db.execute(stmt).scalars().unique().all()
        return [TorrentSchema.model_validate(t) for t in results]

    def get_all_shows_with_torrents(self) -> list[ShowSchema]:
        stmt = (
            select(Show)
            .distinct()
            .join(Season, Show.id == Season.show_id)
            .join(Episode, Season.id == Episode.season_id)
            .join(EpisodeFile, Episode.id == EpisodeFile.episode_id)
            .join(TorrentModel, EpisodeFile.torrent_id == TorrentModel.id)
            .options(joinedload(Show.seasons).joinedload(Season.episodes))
            .order_by(Show.name)
        )
        results = self.db.execute(stmt).scalars().unique().all()
        return [ShowSchema.model_validate(show) for show in results]

    def get_seasons_by_torrent_id(self, torrent_id: TorrentId) -> list[SeasonNumber]:
        stmt = (
            select(Season.number)
            .distinct()
            .join(Episode, Episode.season_id == Season.id)
            .join(EpisodeFile, EpisodeFile.episode_id == Episode.id)
            .where(EpisodeFile.torrent_id == torrent_id)
        )
        results = self.db.execute(stmt).scalars().unique().all()
        return [SeasonNumber(x) for x in results]

    def get_episodes_by_torrent_id(self, torrent_id: TorrentId) -> list[EpisodeNumber]:
        stmt = (
            select(Episode.number)
            .distinct()
            .join(EpisodeFile, EpisodeFile.episode_id == Episode.id)
            .where(EpisodeFile.torrent_id == torrent_id)
            .order_by(Episode.number)
        )
        episode_numbers = self.db.execute(stmt).scalars().all()
        return [EpisodeNumber(n) for n in episode_numbers]

    def get_show_by_season_id(self, season_id: SeasonId) -> ShowSchema:
        stmt = (
            select(Show)
            .join(Season, Show.id == Season.show_id)
            .where(Season.id == season_id)
            .options(joinedload(Show.seasons).joinedload(Season.episodes))
        )
        result = self.db.execute(stmt).unique().scalar_one_or_none()
        if not result:
            msg = f"Show for season {season_id} not found"
            raise NotFoundError(msg)
        return ShowSchema.model_validate(result)

    def add_season_to_show(
        self, show_id: ShowId, season_data: SeasonSchema
    ) -> SeasonSchema:
        db_show = self.db.get(Show, show_id)
        if not db_show:
            msg = f"Show {show_id} not found"
            raise NotFoundError(msg)
        stmt = select(Season).where(
            Season.show_id == show_id, Season.number == season_data.number
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            return SeasonSchema.model_validate(existing)
        db_season = Season(
            id=season_data.id,
            show_id=show_id,
            number=season_data.number,
            external_id=season_data.external_id,
            name=season_data.name,
            overview=season_data.overview,
            episodes=[
                Episode(
                    id=ep_schema.id,
                    number=ep_schema.number,
                    external_id=ep_schema.external_id,
                    title=ep_schema.title,
                    overview=ep_schema.overview,
                )
                for ep_schema in season_data.episodes
            ],
        )
        self.db.add(db_season)
        try:
            self.db.commit()
            self.db.refresh(db_season)
        except IntegrityError as e:
            self.db.rollback()
            msg = f"Integrity error: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return SeasonSchema.model_validate(db_season)

    def add_episode_to_season(
        self, season_id: SeasonId, episode_data: EpisodeSchema
    ) -> EpisodeSchema:
        db_season = self.db.get(Season, season_id)
        if not db_season:
            msg = f"Season {season_id} not found"
            raise NotFoundError(msg)
        stmt = select(Episode).where(
            Episode.season_id == season_id, Episode.number == episode_data.number
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            return EpisodeSchema.model_validate(existing)
        db_episode = Episode(
            id=episode_data.id,
            season_id=season_id,
            number=episode_data.number,
            external_id=episode_data.external_id,
            title=episode_data.title,
            overview=episode_data.overview,
        )
        self.db.add(db_episode)
        try:
            self.db.commit()
            self.db.refresh(db_episode)
        except IntegrityError as e:
            self.db.rollback()
            msg = f"Integrity error: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return EpisodeSchema.model_validate(db_episode)

    def update_show_attributes(
        self,
        show_id: ShowId,
        name: str | None = None,
        overview: str | None = None,
        year: int | None = None,
        ended: bool | None = None,
        continuous_download: bool | None = None,
        imdb_id: str | None = None,
    ) -> ShowSchema:
        return self.update_media_attributes_base(
            media_id=show_id,
            model_class=Show,
            name=name,
            overview=overview,
            year=year,
            ended=ended,
            continuous_download=continuous_download,
            imdb_id=imdb_id,
        )

    def update_season_attributes(
        self, season_id: SeasonId, name: str | None = None, overview: str | None = None
    ) -> SeasonSchema:
        db_season = self.db.get(Season, season_id)
        if not db_season:
            msg = f"Season {season_id} not found"
            raise NotFoundError(msg)
        updated = False
        if name is not None and db_season.name != name:
            db_season.name = name
            updated = True
        if overview is not None and db_season.overview != overview:
            db_season.overview = overview
            updated = True
        if updated:
            try:
                self.db.commit()
                self.db.refresh(db_season)
            except SQLAlchemyError:
                self.db.rollback()
                raise
        return SeasonSchema.model_validate(db_season)

    def update_episode_attributes(
        self,
        episode_id: EpisodeId,
        title: str | None = None,
        overview: str | None = None,
    ) -> EpisodeSchema:
        db_episode = self.db.get(Episode, episode_id)
        if not db_episode:
            msg = f"Episode {episode_id} not found"
            raise NotFoundError(msg)
        updated = False
        if title is not None and db_episode.title != title:
            db_episode.title = title
            updated = True
        if overview is not None and db_episode.overview != overview:
            db_episode.overview = overview
            updated = True
        if updated:
            try:
                self.db.commit()
                self.db.refresh(db_episode)
            except SQLAlchemyError:
                self.db.rollback()
                raise
        return EpisodeSchema.model_validate(db_episode)
