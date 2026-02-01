import pprint
import re
import shutil
from pathlib import Path
from typing import overload

from sqlalchemy.exc import IntegrityError

from media_manager.config import MediaManagerConfig
from media_manager.database import get_session
from media_manager.exceptions import InvalidConfigError, NotFoundError, RenameError
from media_manager.indexer.repository import IndexerRepository
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.indexer.service import IndexerService
from media_manager.indexer.utils import evaluate_indexer_query_results
from media_manager.metadataProvider.abstract_metadata_provider import (
    AbstractMetadataProvider,
)
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult
from media_manager.metadataProvider.tmdb import TmdbMetadataProvider
from media_manager.metadataProvider.tvdb import TvdbMetadataProvider
from media_manager.notification.repository import NotificationRepository
from media_manager.notification.service import NotificationService
from media_manager.schemas import MediaImportSuggestion
from media_manager.torrent.repository import TorrentRepository
from media_manager.torrent.schemas import (
    Quality,
    QualityStrings,
    Torrent,
    TorrentStatus,
)
from media_manager.torrent.service import TorrentService
from media_manager.torrent.utils import (
    extract_external_id_from_string,
    get_files_for_import,
    get_importable_media_directories,
    import_file,
    remove_special_characters,
    remove_special_chars_and_parentheses,
)
from media_manager.tv import log
from media_manager.tv.repository import TvRepository
from media_manager.tv.schemas import (
    Episode as EpisodeSchema,
)
from media_manager.tv.schemas import (
    EpisodeId,
    PublicSeason,
    PublicSeasonFile,
    PublicShow,
    RichSeasonRequest,
    RichSeasonTorrent,
    RichShowTorrent,
    Season,
    SeasonFile,
    SeasonId,
    SeasonRequest,
    SeasonRequestId,
    Show,
    ShowId,
)


class TvService:
    def __init__(
        self,
        tv_repository: TvRepository,
        torrent_service: TorrentService,
        indexer_service: IndexerService,
        notification_service: NotificationService,
    ) -> None:
        self.tv_repository = tv_repository
        self.torrent_service = torrent_service
        self.indexer_service = indexer_service
        self.notification_service = notification_service

    def add_show(
        self,
        external_id: int,
        metadata_provider: AbstractMetadataProvider,
        language: str | None = None,
    ) -> Show:
        """
        Add a new show to the database.

        :param external_id: The ID of the show in the metadata provider\'s system.
        :param metadata_provider: The name of the metadata provider.
        :param language: Optional language code (ISO 639-1) to fetch metadata in.
        """
        show_with_metadata = metadata_provider.get_show_metadata(
            show_id=external_id, language=language
        )
        saved_show = self.tv_repository.save_show(show=show_with_metadata)
        metadata_provider.download_show_poster_image(show=saved_show)
        return saved_show

    def add_season_request(self, season_request: SeasonRequest) -> SeasonRequest:
        """
        Add a new season request.

        :param season_request: The season request to add.
        :return: The added season request.
        """
        return self.tv_repository.add_season_request(season_request=season_request)

    def get_season_request_by_id(
        self, season_request_id: SeasonRequestId
    ) -> SeasonRequest | None:
        """
        Get a season request by its ID.

        :param season_request_id: The ID of the season request.
        :return: The season request or None if not found.
        """
        return self.tv_repository.get_season_request(
            season_request_id=season_request_id
        )

    def get_total_downloaded_episoded_count(self) -> int:
        """
        Get total number of downloaded episodes.
        """

        return self.tv_repository.get_total_downloaded_episodes_count()

    def update_season_request(self, season_request: SeasonRequest) -> SeasonRequest:
        """
        Update an existing season request.

        :param season_request: The season request to update.
        :return: The updated season request.
        """
        self.tv_repository.delete_season_request(season_request_id=season_request.id)
        return self.tv_repository.add_season_request(season_request=season_request)

    def set_show_library(self, show: Show, library: str) -> None:
        self.tv_repository.set_show_library(show_id=show.id, library=library)

    def delete_season_request(self, season_request_id: SeasonRequestId) -> None:
        """
        Delete a season request by its ID.

        :param season_request_id: The ID of the season request to delete.
        """
        self.tv_repository.delete_season_request(season_request_id=season_request_id)

    def delete_show(
        self,
        show: Show,
        delete_files_on_disk: bool = False,
        delete_torrents: bool = False,
    ) -> None:
        """
        Delete a show from the database, optionally deleting files and torrents.

        :param show: The show to delete.
        :param delete_files_on_disk: Whether to delete the show's files from disk.
        :param delete_torrents: Whether to delete associated torrents from the torrent client.
        """
        if delete_files_on_disk or delete_torrents:
            log.debug(f"Deleting ID: {show.id} - Name: {show.name}")

            if delete_files_on_disk:
                show_dir = self.get_root_show_directory(show=show)

                log.debug(f"Attempt to delete show directory: {show_dir}")
                if show_dir.exists() and show_dir.is_dir():
                    shutil.rmtree(show_dir)
                    log.info(f"Deleted show directory: {show_dir}")

            if delete_torrents:
                torrents = self.tv_repository.get_torrents_by_show_id(show_id=show.id)
                for torrent in torrents:
                    try:
                        self.torrent_service.cancel_download(torrent, delete_files=True)
                        log.info(f"Deleted torrent: {torrent.hash}")
                    except Exception:
                        log.warning(
                            f"Failed to delete torrent {torrent.hash}", exc_info=True
                        )

        self.tv_repository.delete_show(show_id=show.id)

    def get_public_season_files_by_season_id(
        self, season: Season
    ) -> list[PublicSeasonFile]:
        """
        Get all public season files for a given season.

        :param season: The season object.
        :return: A list of public season files.
        """
        season_files = self.tv_repository.get_season_files_by_season_id(
            season_id=season.id
        )
        public_season_files = [PublicSeasonFile.model_validate(x) for x in season_files]
        result = []
        for season_file in public_season_files:
            if self.season_file_exists_on_file(season_file=season_file):
                season_file.downloaded = True
            result.append(season_file)
        return result

    @overload
    def check_if_show_exists(self, *, external_id: int, metadata_provider: str) -> bool:
        """
        Check if a show exists in the database.

        :param external_id: The external ID of the show.
        :param metadata_provider: The metadata provider.
        :return: True if the show exists, False otherwise.
        """

    @overload
    def check_if_show_exists(self, *, show_id: ShowId) -> bool:
        """
        Check if a show exists in the database.

        :param show_id: The ID of the show.
        :return: True if the show exists, False otherwise.
        """

    def check_if_show_exists(
        self, *, external_id=None, metadata_provider=None, show_id=None
    ) -> bool:
        if not (external_id is None or metadata_provider is None):
            try:
                self.tv_repository.get_show_by_external_id(
                    external_id=external_id, metadata_provider=metadata_provider
                )
            except NotFoundError:
                return False
        elif show_id is not None:
            try:
                self.tv_repository.get_show_by_id(show_id=show_id)
            except NotFoundError:
                return False
        else:
            msg = "Use one of the provided overloads for this function!"
            raise ValueError(msg)

        return True

    def get_all_available_torrents_for_a_season(
        self,
        season_number: int,
        show_id: ShowId,
        search_query_override: str | None = None,
    ) -> list[IndexerQueryResult]:
        """
        Get all available torrents for a given season.

        :param season_number: The number of the season.
        :param show_id: The ID of the show.
        :param search_query_override: Optional override for the search query.
        :return: A list of indexer query results.
        """

        if search_query_override:
            return self.indexer_service.search(query=search_query_override, is_tv=True)

        show = self.tv_repository.get_show_by_id(show_id=show_id)

        torrents = self.indexer_service.search_season(
            show=show, season_number=season_number
        )

        results = [torrent for torrent in torrents if season_number in torrent.season]

        return evaluate_indexer_query_results(
            is_tv=True, query_results=results, media=show
        )

    def get_all_shows(self) -> list[Show]:
        """
        Get all shows.

        :return: A list of all shows.
        """
        return self.tv_repository.get_shows()

    def search_for_show(
        self, query: str, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        """
        Search for shows using a given query.

        :param query: The search query.
        :param metadata_provider: The metadata provider to search.
        :return: A list of metadata provider show search results.
        """
        results = metadata_provider.search_show(query)
        for result in results:
            if self.check_if_show_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            ):
                result.added = True

                try:
                    show = self.tv_repository.get_show_by_external_id(
                        external_id=result.external_id,
                        metadata_provider=metadata_provider.name,
                    )
                    result.id = show.id
                except Exception:
                    log.error(
                        f"Unable to find internal show ID for {result.external_id} on {metadata_provider.name}"
                    )
        return results

    def get_popular_shows(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MetaDataProviderSearchResult]:
        """
        Get popular shows from a given metadata provider.

        :param metadata_provider: The metadata provider to use.
        :return: A list of metadata provider show search results.
        """
        results = metadata_provider.search_show()

        return [
            result
            for result in results
            if not self.check_if_show_exists(
                external_id=result.external_id, metadata_provider=metadata_provider.name
            )
        ]

    def get_public_show_by_id(self, show: Show) -> PublicShow:
        """
        Get a public show from a Show object.

        :param show: The show object.
        :return: A public show.
        """
        seasons = [PublicSeason.model_validate(season) for season in show.seasons]
        for season in seasons:
            season.downloaded = self.is_season_downloaded(season_id=season.id)
        public_show = PublicShow.model_validate(show)
        public_show.seasons = seasons
        return public_show

    def get_show_by_id(self, show_id: ShowId) -> Show:
        """
        Get a show by its ID.

        :param show_id: The ID of the show.
        :return: The show.
        """
        return self.tv_repository.get_show_by_id(show_id=show_id)

    def is_season_downloaded(self, season_id: SeasonId) -> bool:
        """
        Check if a season is downloaded.

        :param season_id: The ID of the season.
        :return: True if the season is downloaded, False otherwise.
        """
        season_files = self.tv_repository.get_season_files_by_season_id(
            season_id=season_id
        )
        for season_file in season_files:
            if self.season_file_exists_on_file(season_file=season_file):
                return True
        return False

    def season_file_exists_on_file(self, season_file: SeasonFile) -> bool:
        """
        Check if a season file exists on the filesystem.

        :param season_file: The season file to check.
        :return: True if the file exists, False otherwise.
        """
        if season_file.torrent_id is None:
            return True
        try:
            torrent_file = self.torrent_service.get_torrent_by_id(
                torrent_id=season_file.torrent_id
            )

            if torrent_file.imported:
                return True
        except RuntimeError:
            log.exception("Error retrieving torrent")

        return False

    def get_show_by_external_id(
        self, external_id: int, metadata_provider: str
    ) -> Show | None:
        """
        Get a show by its external ID and metadata provider.

        :param external_id: The external ID of the show.
        :param metadata_provider: The metadata provider.
        :return: The show or None if not found.
        """
        return self.tv_repository.get_show_by_external_id(
            external_id=external_id, metadata_provider=metadata_provider
        )

    def get_season(self, season_id: SeasonId) -> Season:
        """
        Get a season by its ID.

        :param season_id: The ID of the season.
        :return: The season.
        """
        return self.tv_repository.get_season(season_id=season_id)

    def get_all_season_requests(self) -> list[RichSeasonRequest]:
        """
        Get all season requests.

        :return: A list of rich season requests.
        """
        return self.tv_repository.get_season_requests()

    def get_torrents_for_show(self, show: Show) -> RichShowTorrent:
        """
        Get torrents for a given show.

        :param show: The show.
        :return: A rich show torrent.
        """
        show_torrents = self.tv_repository.get_torrents_by_show_id(show_id=show.id)
        rich_season_torrents = []
        for show_torrent in show_torrents:
            seasons = self.tv_repository.get_seasons_by_torrent_id(
                torrent_id=show_torrent.id
            )
            season_files = self.torrent_service.get_season_files_of_torrent(
                torrent=show_torrent
            )
            file_path_suffix = season_files[0].file_path_suffix if season_files else ""
            season_torrent = RichSeasonTorrent(
                torrent_id=show_torrent.id,
                torrent_title=show_torrent.title,
                status=show_torrent.status,
                quality=show_torrent.quality,
                imported=show_torrent.imported,
                seasons=seasons,
                file_path_suffix=file_path_suffix,
                usenet=show_torrent.usenet,
            )
            rich_season_torrents.append(season_torrent)
        return RichShowTorrent(
            show_id=show.id,
            name=show.name,
            year=show.year,
            metadata_provider=show.metadata_provider,
            torrents=rich_season_torrents,
        )

    def get_all_shows_with_torrents(self) -> list[RichShowTorrent]:
        """
        Get all shows with torrents.

        :return: A list of rich show torrents.
        """
        shows = self.tv_repository.get_all_shows_with_torrents()
        return [self.get_torrents_for_show(show=show) for show in shows]

    def download_torrent(
        self,
        public_indexer_result_id: IndexerQueryResultId,
        show_id: ShowId,
        override_show_file_path_suffix: str = "",
    ) -> Torrent:
        """
        Download a torrent for a given indexer result and show.

        :param public_indexer_result_id: The ID of the indexer result.
        :param show_id: The ID of the show.
        :param override_show_file_path_suffix: Optional override for the file path suffix.
        :return: The downloaded torrent.
        """
        indexer_result = self.indexer_service.get_result(
            result_id=public_indexer_result_id
        )
        show_torrent = self.torrent_service.download(indexer_result=indexer_result)
        self.torrent_service.pause_download(torrent=show_torrent)

        try:
            for season_number in indexer_result.season:
                season = self.tv_repository.get_season_by_number(
                    season_number=season_number, show_id=show_id
                )
                season_file = SeasonFile(
                    season_id=season.id,
                    quality=indexer_result.quality,
                    torrent_id=show_torrent.id,
                    file_path_suffix=override_show_file_path_suffix,
                )
                self.tv_repository.add_season_file(season_file=season_file)
        except IntegrityError:
            log.error(
                f"Season file for season {season.id} and quality {indexer_result.quality} already exists, skipping."
            )
            self.torrent_service.cancel_download(
                torrent=show_torrent, delete_files=True
            )
            raise
        else:
            log.info(
                f"Successfully added season files for torrent {show_torrent.title} and show ID {show_id}"
            )
            self.torrent_service.resume_download(torrent=show_torrent)

        return show_torrent

    def download_approved_season_request(
        self, season_request: SeasonRequest, show: Show
    ) -> bool:
        """
        Download an approved season request.

        :param season_request: The season request to download.
        :param show: The Show object.
        :return: True if the download was successful, False otherwise.
        :raises ValueError: If the season request is not authorized.
        """
        if not season_request.authorized:
            msg = f"Season request {season_request.id} is not authorized for download"
            raise ValueError(msg)

        log.info(f"Downloading approved season request {season_request.id}")

        season = self.get_season(season_id=season_request.season_id)
        torrents = self.get_all_available_torrents_for_a_season(
            season_number=season.number, show_id=show.id
        )
        available_torrents: list[IndexerQueryResult] = []

        for torrent in torrents:
            if (
                (torrent.quality.value < season_request.wanted_quality.value)
                or (torrent.quality.value > season_request.min_quality.value)
                or (torrent.seeders < 3)
            ):
                log.info(
                    f"Skipping torrent {torrent.title} with quality {torrent.quality} for season {season.id}, because it does not match the requested quality {season_request.wanted_quality}"
                )
            elif torrent.season != [season.number]:
                log.info(
                    f"Skipping torrent {torrent.title} with quality {torrent.quality} for season {season.id}, because it contains to many/wrong seasons {torrent.season} (wanted: {season.number})"
                )
            else:
                available_torrents.append(torrent)
                log.info(
                    f"Taking torrent {torrent.title} with quality {torrent.quality} for season {season.id} into consideration"
                )

        if len(available_torrents) == 0:
            log.warning(
                f"No torrents matching criteria were found (wanted quality: {season_request.wanted_quality}, min_quality: {season_request.min_quality} for season {season.id})"
            )
            return False

        available_torrents.sort()

        torrent = self.torrent_service.download(indexer_result=available_torrents[0])
        season_file = SeasonFile(
            season_id=season.id,
            quality=torrent.quality,
            torrent_id=torrent.id,
            file_path_suffix=QualityStrings[torrent.quality.name].value.upper(),
        )
        try:
            self.tv_repository.add_season_file(season_file=season_file)
        except IntegrityError:
            log.warning(
                f"Season file for season {season.id} and quality {torrent.quality} already exists, skipping."
            )
        self.delete_season_request(season_request.id)
        return True

    def get_root_show_directory(self, show: Show) -> Path:
        misc_config = MediaManagerConfig().misc
        show_directory_name = f"{remove_special_characters(show.name)} ({show.year}) [{show.metadata_provider}id-{show.external_id}]"
        log.debug(
            f"Show {show.name} without special characters: {remove_special_characters(show.name)}"
        )

        if show.library != "Default":
            for library in misc_config.tv_libraries:
                if library.name == show.library:
                    log.debug(
                        f"Using library {library.name} for show {show.name} ({show.year})"
                    )
                    return Path(library.path) / show_directory_name
            else:
                log.warning(
                    f"Library {show.library} not defined in config, using default TV directory."
                )
        return misc_config.tv_directory / show_directory_name

    def get_root_season_directory(self, show: Show, season_number: int) -> Path:
        return self.get_root_show_directory(show) / Path(f"Season {season_number}")

    def import_episode(
        self,
        show: Show,
        season: Season,
        episode_number: int,
        video_files: list[Path],
        subtitle_files: list[Path],
        file_path_suffix: str = "",
    ) -> bool:
        episode_file_name = f"{remove_special_characters(show.name)} S{season.number:02d}E{episode_number:02d}"
        if file_path_suffix != "":
            episode_file_name += f" - {file_path_suffix}"
        pattern = (
            r".*[. ]S0?" + str(season.number) + r"E0?" + str(episode_number) + r"[. ].*"
        )
        subtitle_pattern = pattern + r"[. ]([A-Za-z]{2})[. ]srt"
        target_file_name = (
            self.get_root_season_directory(show=show, season_number=season.number)
            / episode_file_name
        )

        # import subtitle
        for subtitle_file in subtitle_files:
            regex_result = re.search(
                subtitle_pattern, subtitle_file.name, re.IGNORECASE
            )
            if regex_result:
                language_code = regex_result.group(1)
                target_subtitle_file = target_file_name.with_suffix(
                    f".{language_code}.srt"
                )
                import_file(target_file=target_subtitle_file, source_file=subtitle_file)
            else:
                log.debug(
                    f"Didn't find any pattern {subtitle_pattern} in subtitle file: {subtitle_file.name}"
                )

        # import episode videos
        for file in video_files:
            if re.search(pattern, file.name, re.IGNORECASE):
                target_video_file = target_file_name.with_suffix(file.suffix)
                import_file(target_file=target_video_file, source_file=file)
                return True
        else:
            msg = f"Could not find any video file for episode {episode_number} of show {show.name} S{season.number}"
            raise Exception(msg)  # noqa: TRY002 # TODO: resolve this

    def import_season(
        self,
        show: Show,
        season: Season,
        video_files: list[Path],
        subtitle_files: list[Path],
        file_path_suffix: str = "",
    ) -> tuple[bool, int]:
        season_path = self.get_root_season_directory(
            show=show, season_number=season.number
        )
        success = True
        imported_episodes_count = 0
        try:
            season_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.exception(f"Could not create path {season_path}")
            msg = f"Could not create path {season_path}"
            raise Exception(msg) from e  # noqa: TRY002 # TODO: resolve this

        for episode in season.episodes:
            try:
                imported = self.import_episode(
                    show=show,
                    subtitle_files=subtitle_files,
                    video_files=video_files,
                    season=season,
                    episode_number=episode.number,
                    file_path_suffix=file_path_suffix,
                )
                if imported:
                    imported_episodes_count += 1

            except Exception:
                # Send notification about missing episode file
                if self.notification_service:
                    self.notification_service.send_notification_to_all_providers(
                        title="Missing Episode File",
                        message=f"No video file found for S{season.number:02d}E{episode.number:02d} for show {show.name}. Manual intervention may be required.",
                    )
                success = False
                log.warning(
                    f"S{season.number}E{episode.number} not found when trying to import episode for show {show.name}."
                )
        return success, imported_episodes_count

    def import_torrent_files(self, torrent: Torrent, show: Show) -> None:
        """
        Organizes files from a torrent into the TV directory structure, mapping them to seasons and episodes.
        :param torrent: The Torrent object
        :param show: The Show object
        """

        video_files, subtitle_files, _all_files = get_files_for_import(torrent=torrent)

        success: list[bool] = []

        log.debug(
            f"Importing these {len(video_files)} files:\n" + pprint.pformat(video_files)
        )

        season_files = self.torrent_service.get_season_files_of_torrent(torrent=torrent)
        log.info(
            f"Found {len(season_files)} season files associated with torrent {torrent.title}"
        )

        for season_file in season_files:
            season = self.get_season(season_id=season_file.season_id)
            season_import_success, _imported_episodes_count = self.import_season(
                show=show,
                season=season,
                video_files=video_files,
                subtitle_files=subtitle_files,
                file_path_suffix=season_file.file_path_suffix,
            )
            success.append(season_import_success)
            if season_import_success:
                log.info(
                    f"Season {season.number} successfully imported from torrent {torrent.title}"
                )
            else:
                log.warning(
                    f"Season {season.number} failed to import from torrent {torrent.title}"
                )

        log.info(
            f"Finished importing files for torrent {torrent.title} {'without' if all(success) else 'with'} errors"
        )

        if all(success):
            torrent.imported = True
            self.torrent_service.torrent_repository.save_torrent(torrent=torrent)

            # Send successful season download notification
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="TV Show imported successfully",
                    message=f"Successfully imported {show.name} ({show.year}) from torrent {torrent.title}.",
                )
        else:
            if self.notification_service:
                self.notification_service.send_notification_to_all_providers(
                    title="Failed to import TV Show",
                    message=f"Importing {show.name} ({show.year}) from torrent {torrent.title} completed with errors. Please check the logs for details.",
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
                log.debug(
                    f"Updating existing season {existing_season.number} for show {db_show.name}"
                )
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
                    if fresh_episode_data.number in existing_episode_external_ids:
                        # Update existing episode
                        existing_episode = existing_episode_external_ids[
                            fresh_episode_data.external_id
                        ]
                        log.debug(
                            f"Updating existing episode {existing_episode.number} for season {existing_season.number}"
                        )
                        self.tv_repository.update_episode_attributes(
                            episode_id=existing_episode.id,
                            title=fresh_episode_data.title,
                        )
                    else:
                        # Add new episode
                        log.debug(
                            f"Adding new episode {fresh_episode_data.number} to season {existing_season.number}"
                        )
                        episode_schema = EpisodeSchema(
                            id=EpisodeId(fresh_episode_data.id),
                            number=fresh_episode_data.number,
                            external_id=fresh_episode_data.external_id,
                            title=fresh_episode_data.title,
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
                    EpisodeSchema(
                        id=EpisodeId(ep_data.id),
                        number=ep_data.number,
                        external_id=ep_data.external_id,
                        title=ep_data.title,
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

        log.info(f"Successfully updated metadata for show ID: {db_show.id}")
        metadata_provider.download_show_poster_image(show=updated_show)
        return updated_show

    def set_show_continuous_download(
        self, show: Show, continuous_download: bool
    ) -> Show:
        """
        Set the continuous download flag for a show.

        :param show: The show object.
        :param continuous_download: True to enable continuous download, False to disable.
        :return: The updated Show object.
        """
        return self.tv_repository.update_show_attributes(
            show_id=show.id, continuous_download=continuous_download
        )

    def get_import_candidates(
        self, tv_show: Path, metadata_provider: AbstractMetadataProvider
    ) -> MediaImportSuggestion:
        search_result = self.search_for_show(
            remove_special_chars_and_parentheses(tv_show.name), metadata_provider
        )
        import_candidates = MediaImportSuggestion(
            directory=tv_show, candidates=search_result
        )
        log.debug(
            f"Found {len(import_candidates.candidates)} candidates for {import_candidates.directory}"
        )
        return import_candidates

    def import_existing_tv_show(self, tv_show: Show, source_directory: Path) -> None:
        new_source_path = source_directory.parent / ("." + source_directory.name)
        try:
            source_directory.rename(new_source_path)
        except Exception as e:
            log.exception(f"Failed to rename {source_directory} to {new_source_path}")
            raise RenameError from e

        video_files, subtitle_files, _all_files = get_files_for_import(
            directory=new_source_path
        )
        for season in tv_show.seasons:
            success, imported_episode_count = self.import_season(
                show=tv_show,
                season=season,
                video_files=video_files,
                subtitle_files=subtitle_files,
                file_path_suffix="IMPORTED",
            )
            season_file = SeasonFile(
                season_id=season.id,
                quality=Quality.unknown,
                file_path_suffix="IMPORTED",
                torrent_id=None,
            )
            if success or imported_episode_count > (len(season.episodes) / 2):
                self.tv_repository.add_season_file(season_file=season_file)

    def get_importable_tv_shows(
        self, metadata_provider: AbstractMetadataProvider
    ) -> list[MediaImportSuggestion]:
        tv_directory = MediaManagerConfig().misc.tv_directory
        import_suggestions: list[MediaImportSuggestion] = []
        candidate_dirs = get_importable_media_directories(tv_directory)

        for item in candidate_dirs:
            metadata, external_id = extract_external_id_from_string(item.name)
            if metadata is not None and external_id is not None:
                try:
                    self.tv_repository.get_show_by_external_id(
                        external_id=external_id,
                        metadata_provider=metadata,
                    )
                    log.debug(
                        f"Show {item.name} already exists in the database, skipping import suggestion."
                    )
                    continue
                except NotFoundError:
                    log.debug(
                        f"Show {item.name} not found in database, checking for import candidates."
                    )

            import_suggestion = self.get_import_candidates(
                tv_show=item, metadata_provider=metadata_provider
            )
            import_suggestions.append(import_suggestion)

        log.debug(f"Detected {len(import_suggestions)} importable TV shows.")
        return import_suggestions


def auto_download_all_approved_season_requests() -> None:
    """
    Auto download all approved season requests.
    This is a standalone function as it creates its own DB session.
    """
    with next(get_session()) as db:
        tv_repository = TvRepository(db=db)
        torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
        indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
        notification_service = NotificationService(
            notification_repository=NotificationRepository(db=db)
        )
        tv_service = TvService(
            tv_repository=tv_repository,
            torrent_service=torrent_service,
            indexer_service=indexer_service,
            notification_service=notification_service,
        )

        log.info("Auto downloading all approved season requests")
        season_requests = tv_repository.get_season_requests()
        log.info(f"Found {len(season_requests)} season requests to process")
        count = 0

        for season_request in season_requests:
            if season_request.authorized:
                log.info(f"Processing season request {season_request.id} for download")
                show = tv_repository.get_show_by_season_id(
                    season_id=season_request.season_id
                )
                if tv_service.download_approved_season_request(
                    season_request=season_request, show=show
                ):
                    count += 1
                else:
                    log.warning(
                        f"Failed to download season request {season_request.id} for show {show.name}"
                    )

        log.info(f"Auto downloaded {count} approved season requests")
        db.commit()


def import_all_show_torrents() -> None:
    with next(get_session()) as db:
        tv_repository = TvRepository(db=db)
        torrent_service = TorrentService(torrent_repository=TorrentRepository(db=db))
        indexer_service = IndexerService(indexer_repository=IndexerRepository(db=db))
        notification_service = NotificationService(
            notification_repository=NotificationRepository(db=db)
        )
        tv_service = TvService(
            tv_repository=tv_repository,
            torrent_service=torrent_service,
            indexer_service=indexer_service,
            notification_service=notification_service,
        )
        log.info("Importing all torrents")
        torrents = torrent_service.get_all_torrents()
        log.info("Found %d torrents to import", len(torrents))
        for t in torrents:
            try:
                if not t.imported and t.status == TorrentStatus.finished:
                    show = torrent_service.get_show_of_torrent(torrent=t)
                    if show is None:
                        log.warning(
                            f"torrent {t.title} is not a tv torrent, skipping import."
                        )
                        continue
                    tv_service.import_torrent_files(torrent=t, show=show)
            except RuntimeError:
                log.exception(f"Error importing torrent {t.title} for show {show.name}")
        log.info("Finished importing all torrents")
        db.commit()


def update_all_non_ended_shows_metadata() -> None:
    """
    Updates the metadata of all non-ended shows.
    """
    with next(get_session()) as db:
        tv_repository = TvRepository(db=db)
        tv_service = TvService(
            tv_repository=tv_repository,
            torrent_service=TorrentService(torrent_repository=TorrentRepository(db=db)),
            indexer_service=IndexerService(indexer_repository=IndexerRepository(db=db)),
            notification_service=NotificationService(
                notification_repository=NotificationRepository(db=db)
            ),
        )

        log.info("Updating metadata for all non-ended shows")

        shows = [show for show in tv_repository.get_shows() if not show.ended]

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
            updated_show = tv_service.update_show_metadata(
                db_show=show, metadata_provider=metadata_provider
            )

            # Automatically add season requests for new seasons
            existing_seasons = [x.id for x in show.seasons]
            new_seasons = [
                x for x in updated_show.seasons if x.id not in existing_seasons
            ]

            if show.continuous_download:
                for new_season in new_seasons:
                    log.info(
                        f"Automatically adding season request for new season {new_season.number} of show {updated_show.name}"
                    )
                    tv_service.add_season_request(
                        SeasonRequest(
                            min_quality=Quality.sd,
                            wanted_quality=Quality.uhd,
                            season_id=new_season.id,
                            authorized=True,
                        )
                    )

            if updated_show:
                log.debug(
                    f"Added new seasons: {len(new_seasons)} to show: {updated_show.name}"
                )
            else:
                log.warning(f"Failed to update metadata for show: {show.name}")
        db.commit()
