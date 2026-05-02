import logging
from typing import Optional

from media_manager.common.service import BaseMetadataService
from media_manager.exceptions import InvalidConfigError, NotFoundError
from media_manager.metadataProvider.abstract_metadata_provider import AbstractMetadataProvider
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.metadataProvider.tmdb import TmdbMetadataProvider
from media_manager.metadataProvider.tvdb import TvdbMetadataProvider
from media_manager.tv.repository import TvRepository
from media_manager.tv.schemas import Episode, EpisodeId, Season, SeasonId, Show

log = logging.getLogger(__name__)


class TvMetadataService(BaseMetadataService[Show, Show]):
    def __init__(self, tv_repository: TvRepository) -> None:
        super().__init__(repository=tv_repository)
        self.tv_repository = tv_repository

    def add_show(
        self,
        external_id: int,
        metadata_provider: AbstractMetadataProvider,
        language: str | None = None,
    ) -> Show:
        return self.add_media_base(
            external_id=external_id,
            metadata_provider=metadata_provider,
            get_metadata_func=metadata_provider.get_show_metadata,
            save_func=self.tv_repository.save_show,
            download_poster_func=metadata_provider.download_show_poster_image,
            language=language,
        )

    def search_for_show(
        self, query: str, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        return self.search_for_media_base(
            query=query,
            metadata_provider=metadata_provider,
            search_func=metadata_provider.search_show,
            get_by_external_id_func=self.tv_repository.get_show_by_external_id,
        )

    def get_popular_shows(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        return self.get_popular_media_base(
            metadata_provider=metadata_provider,
            search_func=metadata_provider.search_show,
        )

    def update_show_metadata(
        self, db_show: Show, metadata_provider: AbstractMetadataProvider
    ) -> Show | None:
        """
        Updates the metadata of a show.
        This includes adding new seasons and episodes if available from the metadata provider.
        It also updates existing show, season, and episode attributes if they have changed.

        :param metadata_provider: The metadata provider object to fetch fresh data from.
        :param db_show: The Show to update
        :return: The updated Show object, or None if the show is not found or an error occurs.
        """
        log.debug(f"Found show: {db_show.name} for metadata update.")

        # Use stored original_language preference for metadata fetching
        fresh_show_data = metadata_provider.get_show_metadata(
            show_id=db_show.external_id, language=db_show.original_language
        )
        if not fresh_show_data:
            log.warning(
                f"Could not fetch fresh metadata for show {db_show.name} (External ID: {db_show.external_id}) from {db_show.metadata_provider}."
            )
            return db_show
        log.debug(f"Fetched fresh metadata for show: {fresh_show_data.name}")

        self.tv_repository.update_show_attributes(
            show_id=db_show.id,
            name=fresh_show_data.name,
            overview=fresh_show_data.overview,
            year=fresh_show_data.year,
            ended=fresh_show_data.ended,
            imdb_id=fresh_show_data.imdb_id,
            continuous_download=db_show.continuous_download
            if fresh_show_data.ended is False
            else False,
        )

        # Process seasons and episodes
        existing_season_external_ids = {s.external_id: s for s in db_show.seasons}

        for fresh_season_data in fresh_show_data.seasons:
            if fresh_season_data.external_id in existing_season_external_ids:
                # Update existing season
                existing_season = existing_season_external_ids[
                    fresh_season_data.external_id
                ]

                self.tv_repository.update_season_attributes(
                    season_id=existing_season.id,
                    name=fresh_season_data.name,
                    overview=fresh_season_data.overview,
                )

                # Process episodes for this season
                existing_episode_external_ids = {
                    ep.external_id: ep for ep in existing_season.episodes
                }
                for fresh_episode_data in fresh_season_data.episodes:
                    if fresh_episode_data.external_id in existing_episode_external_ids:
                        # Update existing episode
                        existing_episode = existing_episode_external_ids[
                            fresh_episode_data.external_id
                        ]

                        self.tv_repository.update_episode_attributes(
                            episode_id=existing_episode.id,
                            title=fresh_episode_data.title,
                            overview=fresh_episode_data.overview,
                        )
                    else:
                        # Add new episode
                        log.debug(
                            f"Adding new episode {fresh_episode_data.number} to season {existing_season.number}"
                        )
                        episode_schema = Episode(
                            id=EpisodeId(fresh_episode_data.id),
                            number=fresh_episode_data.number,
                            external_id=fresh_episode_data.external_id,
                            title=fresh_episode_data.title,
                            overview=fresh_episode_data.overview,
                        )
                        self.tv_repository.add_episode_to_season(
                            season_id=existing_season.id, episode_data=episode_schema
                        )
            else:
                # Add new season (and its episodes)
                log.debug(
                    f"Adding new season {fresh_season_data.number} to show {db_show.name}"
                )
                episodes_for_schema = [
                    Episode(
                        id=EpisodeId(ep_data.id),
                        number=ep_data.number,
                        external_id=ep_data.external_id,
                        title=ep_data.title,
                        overview=ep_data.overview,
                    )
                    for ep_data in fresh_season_data.episodes
                ]

                season_schema = Season(
                    id=SeasonId(fresh_season_data.id),
                    number=fresh_season_data.number,
                    name=fresh_season_data.name,
                    overview=fresh_season_data.overview,
                    external_id=fresh_season_data.external_id,
                    episodes=episodes_for_schema,
                )
                self.tv_repository.add_season_to_show(
                    show_id=db_show.id, season_data=season_schema
                )

        updated_show = self.tv_repository.get_show_by_id(show_id=db_show.id)

        log.info(f"Successfully updated metadata for show: {updated_show.name}")
        metadata_provider.download_show_poster_image(show=updated_show)
        return updated_show

    def update_all_non_ended_shows_metadata(self) -> None:
        """Updates the metadata of all non-ended shows."""
        log.info("Updating metadata for all non-ended shows")
        shows = [show for show in self.tv_repository.get_shows() if not show.ended]
        log.info(f"Found {len(shows)} non-ended shows to update")
        for show in shows:
            try:
                if show.metadata_provider == "tmdb":
                    metadata_provider = TmdbMetadataProvider()
                elif show.metadata_provider == "tvdb":
                    metadata_provider = TvdbMetadataProvider()
                else:
                    log.error(
                        f"Unsupported metadata provider {show.metadata_provider} for show {show.name}, skipping update."
                    )
                    continue
            except InvalidConfigError:
                log.exception(
                    f"Error initializing metadata provider {show.metadata_provider} for show {show.name}"
                )
                continue
            updated_show = self.update_show_metadata(
                db_show=show, metadata_provider=metadata_provider
            )
            if updated_show:
                log.debug("Updated show metadata", extra={"show": updated_show.name})
            else:
                log.warning(f"Failed to update metadata for show: {show.name}")
