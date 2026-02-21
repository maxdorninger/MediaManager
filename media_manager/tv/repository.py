from sqlalchemy import delete, func, select
from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)
from sqlalchemy.orm import Session, joinedload

from media_manager.exceptions import ConflictError, NotFoundError
from media_manager.torrent.models import Torrent
from media_manager.torrent.schemas import Torrent as TorrentSchema
from media_manager.torrent.schemas import TorrentId
from media_manager.tv import log
from media_manager.tv.models import Season, Show, Episode, SeasonRequest, EpisodeFile
from media_manager.tv.schemas import (
    Episode as EpisodeSchema,
)
from media_manager.tv.schemas import (
    EpisodeId,
    EpisodeNumber,
    SeasonId,
    SeasonNumber,
    SeasonRequestId,
    ShowId,
)
from media_manager.tv.schemas import (
    RichSeasonRequest as RichSeasonRequestSchema,
)
from media_manager.tv.schemas import (
    Season as SeasonSchema,
)
from media_manager.tv.schemas import (
    EpisodeFile as EpisodeFileSchema,
)
from media_manager.tv.schemas import (
    SeasonRequest as SeasonRequestSchema,
)
from media_manager.tv.schemas import (
    Show as ShowSchema,
)


class TvRepository:
    """
    Repository for managing TV shows, seasons, and episodes in the database.
    Provides methods to retrieve, save, and delete shows and seasons.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_show_by_id(self, show_id: ShowId) -> ShowSchema:
        """
        Retrieve a show by its ID, including seasons and episodes.

        :param show_id: The ID of the show to retrieve.
        :return: A Show object if found.
        :raises NotFoundError: If the show with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
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
            return ShowSchema.model_validate(result)
        except SQLAlchemyError:
            log.exception(f"Database error while retrieving show {show_id}")
            raise

    def get_show_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> ShowSchema:
        """
        Retrieve a show by its external ID, including nested seasons and episodes.

        :param external_id: The ID of the show to retrieve.
        :param metadata_provider: The metadata provider associated with the ID.
        :return: A Show object if found.
        :raises NotFoundError: If the show with the given external ID and provider is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
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
            return ShowSchema.model_validate(result)
        except SQLAlchemyError:
            log.exception(
                f"Database error while retrieving show by external_id {external_id}",
            )
            raise

    def get_shows(self) -> list[ShowSchema]:
        """
        Retrieve all shows from the database.

        :return: A list of Show objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(Show).options(
                joinedload(Show.seasons).joinedload(Season.episodes)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [ShowSchema.model_validate(show) for show in results]
        except SQLAlchemyError:
            log.exception("Database error while retrieving all shows")
            raise

    def get_total_downloaded_episodes_count(self) -> int:
        try:
            stmt = (
                select(func.count(Episode.id))
                .select_from(Episode)
                .join(EpisodeFile)
            )
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            log.exception("Database error while calculating downloaded episodes count")
            raise

    def save_show(self, show: ShowSchema) -> ShowSchema:
        """
        Save a new show or update an existing one in the database.

        :param show: The Show object to save.
        :return: The saved Show object.
        :raises ValueError: If a show with the same primary key already exists (on insert).
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_show = self.db.get(Show, show.id) if show.id else None

        if db_show:  # Update existing show
            db_show.external_id = show.external_id
            db_show.metadata_provider = show.metadata_provider
            db_show.name = show.name
            db_show.overview = show.overview
            db_show.year = show.year
            db_show.original_language = show.original_language
            db_show.imdb_id = show.imdb_id
        else:  # Insert new show
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
            return ShowSchema.model_validate(db_show)
        except IntegrityError as e:
            self.db.rollback()
            msg = f"Show with this primary key or unique constraint violation: {e.orig}"
            raise ConflictError(msg) from e
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while saving show {show.name}")
            raise

    def delete_show(self, show_id: ShowId) -> None:
        """
        Delete a show by its ID.

        :param show_id: The ID of the show to delete.
        :raises NotFoundError: If the show with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            show = self.db.get(Show, show_id)
            if not show:
                msg = f"Show with id {show_id} not found."
                raise NotFoundError(msg)
            self.db.delete(show)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error while deleting show {show_id}")
            raise

    def get_season(self, season_id: SeasonId) -> SeasonSchema:
        """
        Retrieve a season by its ID.

        :param season_id: The ID of the season to get.
        :return: A Season object.
        :raises NotFoundError: If the season with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            season = self.db.get(Season, season_id)
            if not season:
                msg = f"Season with id {season_id} not found."
                raise NotFoundError(msg)
            return SeasonSchema.model_validate(season)
        except SQLAlchemyError:
            log.exception(f"Database error while retrieving season {season_id}")
            raise

    def get_episode(self, episode_id: EpisodeId) -> EpisodeSchema:
        """
        Retrieve an episode by its ID.

        :param episode_id: The ID of the episode to get.
        :return: An Episode object.
        :raises NotFoundError: If the episode with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            episode = self.db.get(Episode, episode_id)
            if not episode:
                raise NotFoundError(f"Episode with id {episode_id} not found.")
            return EpisodeSchema.model_validate(episode)
        except SQLAlchemyError as e:
            log.error(f"Database error while retrieving episode {episode_id}: {e}")
            raise

    def get_season_by_episode(self, episode_id: EpisodeId) -> SeasonSchema:
        try:
            stmt = (
                select(Season)
                .join(Season.episodes)
                .where(Episode.id == episode_id)
            )

            season = self.db.scalar(stmt)

            if not season:
                raise NotFoundError(
                    f"Season not found for episode {episode_id}"
                )

            return SeasonSchema.model_validate(season)

        except SQLAlchemyError as e:
            log.error(
                f"Database error while retrieving season for episode "
                f"{episode_id}: {e}"
            )
            raise

    def add_season_request(
        self, season_request: SeasonRequestSchema
    ) -> SeasonRequestSchema:
        """
        Adds a Season to the SeasonRequest table, which marks it as requested.

        :param season_request: The SeasonRequest object to add.
        :return: The added SeasonRequest object.
        :raises IntegrityError: If a similar request already exists or violates constraints.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_model = SeasonRequest(
            id=season_request.id,
            season_id=season_request.season_id,
            wanted_quality=season_request.wanted_quality,
            min_quality=season_request.min_quality,
            requested_by_id=season_request.requested_by.id
            if season_request.requested_by
            else None,
            authorized=season_request.authorized,
            authorized_by_id=season_request.authorized_by.id
            if season_request.authorized_by
            else None,
        )
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            return SeasonRequestSchema.model_validate(db_model)
        except IntegrityError:
            self.db.rollback()
            log.exception("Integrity error while adding season request")
            raise
        except SQLAlchemyError:
            self.db.rollback()
            log.exception("Database error while adding season request")
            raise

    def delete_season_request(self, season_request_id: SeasonRequestId) -> None:
        """
        Removes a SeasonRequest by its ID.

        :param season_request_id: The ID of the season request to delete.
        :raises NotFoundError: If the season request is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = delete(SeasonRequest).where(SeasonRequest.id == season_request_id)
            result = self.db.execute(stmt)
            if result.rowcount == 0:
                self.db.rollback()
                msg = f"SeasonRequest with id {season_request_id} not found."
                raise NotFoundError(msg)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error while deleting season request {season_request_id}"
            )
            raise

    def get_season_by_number(self, season_number: int, show_id: ShowId) -> SeasonSchema:
        """
        Retrieve a season by its number and show ID.

        :param season_number: The number of the season.
        :param show_id: The ID of the show.
        :return: A Season object.
        :raises NotFoundError: If the season is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Season)
                .where(Season.show_id == show_id)
                .where(Season.number == season_number)
                .options(joinedload(Season.episodes), joinedload(Season.show))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Season number {season_number} for show_id {show_id} not found."
                raise NotFoundError(msg)
            return SeasonSchema.model_validate(result)
        except SQLAlchemyError:
            log.exception(
                f"Database error retrieving season {season_number} for show {show_id}"
            )
            raise

    def get_season_requests(self) -> list[RichSeasonRequestSchema]:
        """
        Retrieve all season requests.

        :return: A list of RichSeasonRequest objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(SeasonRequest).options(
                joinedload(SeasonRequest.requested_by),
                joinedload(SeasonRequest.authorized_by),
                joinedload(SeasonRequest.season).joinedload(Season.show),
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [
                RichSeasonRequestSchema(
                    id=SeasonRequestId(x.id),
                    min_quality=x.min_quality,
                    wanted_quality=x.wanted_quality,
                    season_id=SeasonId(x.season_id),
                    show=x.season.show,
                    season=x.season,
                    requested_by=x.requested_by,
                    authorized_by=x.authorized_by,
                    authorized=x.authorized,
                )
                for x in results
            ]
        except SQLAlchemyError:
            log.exception("Database error while retrieving season requests")
            raise

    def add_episode_file(self, episode_file: EpisodeFileSchema) -> EpisodeFileSchema:
        """
        Adds an episode file record to the database.

        :param episode_file: The EpisodeFile object to add.
        :return: The added EpisodeFile object.
        :raises IntegrityError: If the record violates constraints.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_model = EpisodeFile(**episode_file.model_dump())
        try:
            self.db.add(db_model)
            self.db.commit()
            self.db.refresh(db_model)
            return EpisodeFileSchema.model_validate(db_model)
        except IntegrityError as e:
            self.db.rollback()
            log.error(f"Integrity error while adding episode file: {e}")
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            log.error(f"Database error while adding episode file: {e}")
            raise

    def remove_episode_files_by_torrent_id(self, torrent_id: TorrentId) -> int:
        """
        Removes episode file records associated with a given torrent ID.

        :param torrent_id: The ID of the torrent whose episode files are to be removed.
        :return: The number of episode files removed.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = delete(EpisodeFile).where(EpisodeFile.torrent_id == torrent_id)
            result = self.db.execute(stmt)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(
                f"Database error removing episode files for torrent_id {torrent_id}"
            )
            raise
        return result.rowcount

    def set_show_library(self, show_id: ShowId, library: str) -> None:
        """
        Sets the library for a show.

        :param show_id: The ID of the show to update.
        :param library: The library path to set for the show.
        :raises NotFoundError: If the show with the given ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            show = self.db.get(Show, show_id)
            if not show:
                msg = f"Show with id {show_id} not found."
                raise NotFoundError(msg)
            show.library = library
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            log.exception(f"Database error setting library for show {show_id}")
            raise

    def get_episode_files_by_season_id(self, season_id: SeasonId) -> list[EpisodeFileSchema]:
        """
        Retrieve all episode files for a given season ID.

        :param season_id: The ID of the season.
        :return: A list of EpisodeFile objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(EpisodeFile)
                .join(Episode)
                .where(Episode.season_id == season_id)
            )
            results = self.db.execute(stmt).scalars().all()
            return [EpisodeFileSchema.model_validate(ef) for ef in results]
        except SQLAlchemyError:
            log.exception(
                f"Database error retrieving episode files for season_id {season_id}"
            )
            raise

    def get_episode_files_by_episode_id(self, episode_id: EpisodeId) -> list[EpisodeFileSchema]:
        """
        Retrieve all episode files for a given episode ID.

        :param episode_id: The ID of the episode.
        :return: A list of EpisodeFile objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = select(EpisodeFile).where(EpisodeFile.episode_id == episode_id)
            results = self.db.execute(stmt).scalars().all()
            return [EpisodeFileSchema.model_validate(sf) for sf in results]
        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving episode files for episode_id {episode_id}: {e}"
            )
            raise

    def get_torrents_by_show_id(self, show_id: ShowId) -> list[TorrentSchema]:
        """
        Retrieve all torrents associated with a given show ID.

        :param show_id: The ID of the show.
        :return: A list of Torrent objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Torrent)
                .distinct()
                .join(EpisodeFile, EpisodeFile.torrent_id == Torrent.id)
                .join(Episode, Episode.id == EpisodeFile.episode_id)
                .join(Season, Season.id == Episode.season_id)
                .where(Season.show_id == show_id)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [TorrentSchema.model_validate(torrent) for torrent in results]
        except SQLAlchemyError:
            log.exception(f"Database error retrieving torrents for show_id {show_id}")
            raise

    def get_all_shows_with_torrents(self) -> list[ShowSchema]:
        """
        Retrieve all shows that are associated with a torrent, ordered alphabetically by show name.

        :return: A list of Show objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Show)
                .distinct()
                .join(Season, Show.id == Season.show_id)
                .join(Episode, Season.id == Episode.season_id)
                .join(EpisodeFile, Episode.id == EpisodeFile.episode_id)
                .join(Torrent, EpisodeFile.torrent_id == Torrent.id)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
                .order_by(Show.name)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [ShowSchema.model_validate(show) for show in results]
        except SQLAlchemyError:
            log.exception("Database error retrieving all shows with torrents")
            raise

    def get_seasons_by_torrent_id(self, torrent_id: TorrentId) -> list[SeasonNumber]:
        """
        Retrieve season numbers associated with a given torrent ID.

        :param torrent_id: The ID of the torrent.
        :return: A list of SeasonNumber objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Season.number)
                .distinct()
                .join(Episode, Episode.season_id == Season.id)
                .join(EpisodeFile, EpisodeFile.episode_id == Episode.id)
                .where(EpisodeFile.torrent_id == torrent_id)
            )
            results = self.db.execute(stmt).scalars().unique().all()
            return [SeasonNumber(x) for x in results]
        except SQLAlchemyError:
            log.exception(
                f"Database error retrieving season numbers for torrent_id {torrent_id}"
            )
            raise

    def get_episodes_by_torrent_id(self, torrent_id: TorrentId) -> list[EpisodeNumber]:
        """
        Retrieve episode numbers associated with a given torrent ID.

        :param torrent_id: The ID of the torrent.
        :return: A list of EpisodeNumber objects.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Episode.number)
                .join(EpisodeFile, EpisodeFile.episode_id == Episode.id)
                .where(EpisodeFile.torrent_id == torrent_id)
                .order_by(Episode.number)
            )

            episode_numbers = self.db.execute(stmt).scalars().all()

            return [EpisodeNumber(n) for n in sorted(set(episode_numbers))]

        except SQLAlchemyError as e:
            log.error(
                f"Database error retrieving episodes for torrent_id {torrent_id}: {e}"
            )
            raise


    def get_season_request(
        self, season_request_id: SeasonRequestId
    ) -> SeasonRequestSchema:
        """
        Retrieve a season request by its ID.

        :param season_request_id: The ID of the season request.
        :return: A SeasonRequest object.
        :raises NotFoundError: If the season request is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            request = self.db.get(SeasonRequest, season_request_id)
            if not request:
                log.warning(f"Season request with id {season_request_id} not found.")
                msg = f"Season request with id {season_request_id} not found."
                raise NotFoundError(msg)
            return SeasonRequestSchema.model_validate(request)
        except SQLAlchemyError:
            log.exception(
                f"Database error retrieving season request {season_request_id}"
            )
            raise

    def get_show_by_season_id(self, season_id: SeasonId) -> ShowSchema:
        """
        Retrieve a show by one of its season's ID.

        :param season_id: The ID of the season to retrieve the show for.
        :return: A Show object.
        :raises NotFoundError: If the show for the given season ID is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        try:
            stmt = (
                select(Show)
                .join(Season, Show.id == Season.show_id)
                .where(Season.id == season_id)
                .options(joinedload(Show.seasons).joinedload(Season.episodes))
            )
            result = self.db.execute(stmt).unique().scalar_one_or_none()
            if not result:
                msg = f"Show for season_id {season_id} not found."
                raise NotFoundError(msg)
            return ShowSchema.model_validate(result)
        except SQLAlchemyError:
            log.exception(f"Database error retrieving show by season_id {season_id}")
            raise

    def add_season_to_show(
        self, show_id: ShowId, season_data: SeasonSchema
    ) -> SeasonSchema:
        """
        Adds a new season and its episodes to a show.
        If the season number already exists for the show, it returns the existing season.

        :param show_id: The ID of the show to add the season to.
        :param season_data: The SeasonSchema object for the new season.
        :return: The added or existing SeasonSchema object.
        :raises NotFoundError: If the show is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_show = self.db.get(Show, show_id)
        if not db_show:
            msg = f"Show with id {show_id} not found."
            raise NotFoundError(msg)

        stmt = (
            select(Season)
            .where(Season.show_id == show_id)
            .where(Season.number == season_data.number)
        )
        existing_db_season = self.db.execute(stmt).scalar_one_or_none()
        if existing_db_season:
            return SeasonSchema.model_validate(existing_db_season)

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
                )
                for ep_schema in season_data.episodes
            ],
        )

        self.db.add(db_season)
        self.db.commit()
        self.db.refresh(db_season)
        return SeasonSchema.model_validate(db_season)

    def add_episode_to_season(
        self, season_id: SeasonId, episode_data: EpisodeSchema
    ) -> EpisodeSchema:
        """
        Adds a new episode to a season.
        If the episode number already exists for the season, it returns the existing episode.

        :param season_id: The ID of the season to add the episode to.
        :param episode_data: The EpisodeSchema object for the new episode.
        :return: The added or existing EpisodeSchema object.
        :raises NotFoundError: If the season is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_season = self.db.get(Season, season_id)
        if not db_season:
            msg = f"Season with id {season_id} not found."
            raise NotFoundError(msg)

        stmt = (
            select(Episode)
            .where(Episode.season_id == season_id)
            .where(Episode.number == episode_data.number)
        )
        existing_db_episode = self.db.execute(stmt).scalar_one_or_none()
        if existing_db_episode:
            return EpisodeSchema.model_validate(existing_db_episode)

        db_episode = Episode(
            id=episode_data.id,
            season_id=season_id,
            number=episode_data.number,
            external_id=episode_data.external_id,
            title=episode_data.title,
        )

        self.db.add(db_episode)
        self.db.commit()
        self.db.refresh(db_episode)
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
        """
        Update attributes of an existing show.

        :param imdb_id: The new IMDb ID for the show.
        :param continuous_download: The new continuous download status for the show.
        :param show_id: The ID of the show to update.
        :param name: The new name for the show.
        :param overview: The new overview for the show.
        :param year: The new year for the show.
        :param ended: The new ended status for the show.
        :return: The updated ShowSchema object.
        """
        db_show = self.db.get(Show, show_id)
        if not db_show:
            msg = f"Show with id {show_id} not found."
            raise NotFoundError(msg)

        updated = False
        if name is not None and db_show.name != name:
            db_show.name = name
            updated = True
        if overview is not None and db_show.overview != overview:
            db_show.overview = overview
            updated = True
        if year is not None and db_show.year != year:
            db_show.year = year
            updated = True
        if ended is not None and db_show.ended != ended:
            db_show.ended = ended
            updated = True
        if (
            continuous_download is not None
            and db_show.continuous_download != continuous_download
        ):
            db_show.continuous_download = continuous_download
            updated = True
        if imdb_id is not None and db_show.imdb_id != imdb_id:
            db_show.imdb_id = imdb_id
            updated = True
        if updated:
            self.db.commit()
            self.db.refresh(db_show)
        return ShowSchema.model_validate(db_show)

    def update_season_attributes(
        self, season_id: SeasonId, name: str | None = None, overview: str | None = None
    ) -> SeasonSchema:
        """
        Update attributes of an existing season.

        :param season_id: The ID of the season to update.
        :param name: The new name for the season.
        :param overview: The new overview for the season.
        :param external_id: The new external ID for the season.
        :return: The updated SeasonSchema object.
        :raises NotFoundError: If the season is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_season = self.db.get(Season, season_id)
        if not db_season:
            msg = f"Season with id {season_id} not found."
            raise NotFoundError(msg)

        updated = False
        if name is not None and db_season.name != name:
            db_season.name = name
            updated = True
        if overview is not None and db_season.overview != overview:
            db_season.overview = overview
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_season)
        return SeasonSchema.model_validate(db_season)

    def update_episode_attributes(
        self, episode_id: EpisodeId, title: str | None = None
    ) -> EpisodeSchema:
        """
        Update attributes of an existing episode.

        :param episode_id: The ID of the episode to update.
        :param title: The new title for the episode.
        :param external_id: The new external ID for the episode.
        :return: The updated EpisodeSchema object.
        :raises NotFoundError: If the episode is not found.
        :raises SQLAlchemyError: If a database error occurs.
        """
        db_episode = self.db.get(Episode, episode_id)
        if not db_episode:
            msg = f"Episode with id {episode_id} not found."
            raise NotFoundError(msg)

        updated = False
        if title is not None and db_episode.title != title:
            db_episode.title = title
            updated = True

        if updated:
            self.db.commit()
            self.db.refresh(db_episode)
        return EpisodeSchema.model_validate(db_episode)
