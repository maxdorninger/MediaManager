from unittest.mock import MagicMock, patch

import pytest

from media_manager.torrent.schemas import Quality, Torrent, TorrentStatus
from media_manager.tv.schemas import Episode, EpisodeNumber, Season, SeasonNumber, Show
from media_manager.tv.service import TvService

# ── helpers ────────────────────────────────────────────────────────────────────


def make_service():
    return TvService(
        tv_repository=MagicMock(),
        torrent_service=MagicMock(),
        indexer_service=MagicMock(),
        notification_service=MagicMock(),
    )


def make_show(name="Test Show", year=2026):
    return Show(
        name=name,
        overview="",
        year=year,
        external_id=1,
        metadata_provider="tmdb",
        seasons=[],
    )


def make_season(number=1, episodes=None):
    return Season(
        number=SeasonNumber(number),
        name=f"Season {number}",
        overview="",
        external_id=number,
        episodes=episodes or [],
    )


def make_episode(number):
    return Episode(
        number=EpisodeNumber(number), external_id=number, title=f"Episode {number}"
    )


def make_torrent(title="Test Show S01 1080p"):
    return Torrent(
        status=TorrentStatus.finished,
        title=title,
        quality=Quality.fullhd,
        imported=False,
        hash="abc123",
    )


# ── import_episode ─────────────────────────────────────────────────────────────


class TestImportEpisode:
    """
    Focuses on file-pattern matching: separator variants, zero-padding,
    wrong-episode rejection, and subtitle language code extraction.
    """

    @pytest.fixture
    def svc(self):
        return make_service()

    @pytest.fixture
    def show(self):
        return make_show()

    @pytest.fixture
    def season(self):
        return make_season(1)

    @pytest.fixture(autouse=True)
    def mock_config(self, tmp_path):
        with patch("media_manager.tv.service.MediaManagerConfig") as mock_cfg:
            mock_cfg.return_value.misc.tv_directory = tmp_path
            yield

    @pytest.fixture
    def mock_import(self):
        with patch("media_manager.tv.service.import_file") as m:
            yield m

    @pytest.mark.parametrize(
        "filename",
        [
            "Show.S01E01.720p.mkv",  # dot
            "Show S01E01 720p.mkv",  # space
            "Show_S01E01_720p.mkv",  # underscore
            "Show-S01E01-720p.mkv",  # hyphen
            "Show.s01e01.720p.mkv",  # lowercase
            "Show.S1E1.720p.mkv",  # no zero-padding
            "Show.S01E01.mkv",  # no quality token
        ],
    )
    def test_separator_variants(
        self, svc, show, season, mock_import, tmp_path, filename
    ):
        f = tmp_path / filename
        f.touch()
        result = svc.import_episode(
            show=show,
            season=season,
            episode_number=1,
            video_files=[f],
            subtitle_files=[],
        )
        assert result is True
        mock_import.assert_called_once()

    @pytest.mark.parametrize(
        "filenames",
        [
            [],                     # no files at all
            ["Show.S01E02.mkv"],    # right season, wrong episode
            ["Show.S02E01.mkv"],    # right episode number, wrong season
        ],
        ids=["no_files", "wrong_episode", "wrong_season"],
    )
    def test_video_not_found_raises(self, svc, show, season, tmp_path, filenames):
        files = [tmp_path / name for name in filenames]
        for f in files:
            f.touch()
        with pytest.raises(Exception, match="Could not find any video file"):
            svc.import_episode(
                show=show,
                season=season,
                episode_number=1,
                video_files=files,
                subtitle_files=[],
            )

    def test_correct_episode_chosen_from_multiple(
        self, svc, show, season, mock_import, tmp_path
    ):
        ep1 = tmp_path / "Show.S01E01.mkv"
        ep2 = tmp_path / "Show.S01E02.mkv"
        ep1.touch()
        ep2.touch()
        result = svc.import_episode(
            show=show,
            season=season,
            episode_number=1,
            video_files=[ep1, ep2],
            subtitle_files=[],
        )
        assert result is True
        assert mock_import.call_args.kwargs["source_file"] == ep1

    def test_subtitle_language_code_extracted(
        self, svc, show, season, mock_import, tmp_path
    ):
        video = tmp_path / "Show.S01E01.720p.mkv"
        subtitle = tmp_path / "Show.S01E01.720p.en.srt"
        video.touch()
        subtitle.touch()
        svc.import_episode(
            show=show,
            season=season,
            episode_number=1,
            video_files=[video],
            subtitle_files=[subtitle],
        )
        subtitle_calls = [
            c
            for c in mock_import.call_args_list
            if str(c.kwargs["target_file"]).endswith(".srt")
        ]
        assert len(subtitle_calls) == 1
        assert ".en.srt" in str(subtitle_calls[0].kwargs["target_file"])

    def test_subtitle_wrong_episode_skipped(
        self, svc, show, season, mock_import, tmp_path
    ):
        video = tmp_path / "Show.S01E01.mkv"
        subtitle = tmp_path / "Show.S01E02.720p.en.srt"  # episode 2, not 1
        video.touch()
        subtitle.touch()
        svc.import_episode(
            show=show,
            season=season,
            episode_number=1,
            video_files=[video],
            subtitle_files=[subtitle],
        )
        subtitle_calls = [
            c
            for c in mock_import.call_args_list
            if str(c.kwargs["target_file"]).endswith(".srt")
        ]
        assert len(subtitle_calls) == 0


# ── import_season ──────────────────────────────────────────────────────────────


class TestImportSeason:
    @pytest.fixture
    def svc(self):
        return make_service()

    @pytest.fixture
    def show(self):
        return make_show()

    def test_all_episodes_found_returns_success(self, svc, show, tmp_path):
        season = make_season(1, [make_episode(1), make_episode(2)])
        files = [tmp_path / "Show.S01E01.mkv", tmp_path / "Show.S01E02.mkv"]
        for f in files:
            f.touch()
        with (
            patch("media_manager.tv.service.MediaManagerConfig") as mock_cfg,
            patch("media_manager.tv.service.import_file"),
        ):
            mock_cfg.return_value.misc.tv_directory = tmp_path
            success, episodes = svc.import_season(
                show=show, season=season, video_files=files, subtitle_files=[]
            )
        assert success is True
        assert len(episodes) == 2

    def test_missing_episode_returns_partial_failure(self, svc, show, tmp_path):
        season = make_season(1, [make_episode(1), make_episode(2)])
        files = [tmp_path / "Show.S01E01.mkv"]  # episode 2 absent
        files[0].touch()
        with (
            patch("media_manager.tv.service.MediaManagerConfig") as mock_cfg,
            patch("media_manager.tv.service.import_file"),
        ):
            mock_cfg.return_value.misc.tv_directory = tmp_path
            success, episodes = svc.import_season(
                show=show, season=season, video_files=files, subtitle_files=[]
            )
        assert success is False
        assert len(episodes) == 1

    def test_creates_season_directory(self, svc, show, tmp_path):
        season = make_season(2, [make_episode(1)])
        video = tmp_path / "Show.S02E01.mkv"
        video.touch()
        with (
            patch("media_manager.tv.service.MediaManagerConfig") as mock_cfg,
            patch("media_manager.tv.service.import_file"),
        ):
            mock_cfg.return_value.misc.tv_directory = tmp_path
            svc.import_season(
                show=show, season=season, video_files=[video], subtitle_files=[]
            )
        assert (tmp_path / "Test Show (2026) [tmdbid-1]" / "Season 2").is_dir()

    def test_empty_season_succeeds_with_zero_count(self, svc, show, tmp_path):
        season = make_season(1, [])
        with (
            patch("media_manager.tv.service.MediaManagerConfig") as mock_cfg,
            patch("media_manager.tv.service.import_file"),
        ):
            mock_cfg.return_value.misc.tv_directory = tmp_path
            success, episodes = svc.import_season(
                show=show, season=season, video_files=[], subtitle_files=[]
            )
        assert success is True
        assert len(episodes) == 0


# ── import_episode_files_from_torrent ─────────────────────────────────────────


class TestImportEpisodeFilesFromTorrent:
    @pytest.fixture
    def svc(self):
        return make_service()

    @pytest.fixture
    def show(self):
        return make_show()

    @pytest.fixture
    def torrent(self):
        return make_torrent()

    @pytest.fixture(autouse=True)
    def mock_get_files(self):
        with patch(
            "media_manager.tv.service.get_files_for_import", return_value=([], [], [])
        ):
            yield

    def _setup(self, svc, seasons, episodes):
        """Set up one episode file mock per episode, each linked to its season."""
        episode_file_mocks = []
        for episode in episodes:
            ef = MagicMock()
            ef.episode_id = episode.id
            ef.file_path_suffix = ""
            episode_file_mocks.append(ef)
        svc.torrent_service.get_episode_files_of_torrent.return_value = episode_file_mocks
        svc.get_season_by_episode = MagicMock(side_effect=seasons)
        svc.get_episode = MagicMock(side_effect=episodes)
        season_path_mock = MagicMock()
        season_path_mock.exists.return_value = True
        svc.get_root_season_directory = MagicMock(return_value=season_path_mock)

    def test_success_marks_torrent_imported(self, svc, show, torrent):
        episodes = [make_episode(1)]
        self._setup(svc, [make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=True)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        assert torrent.imported is True

    def test_success_saves_torrent(self, svc, show, torrent):
        episodes = [make_episode(1)]
        self._setup(svc, [make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=True)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        svc.torrent_service.torrent_repository.save_torrent.assert_called_once_with(
            torrent=torrent
        )

    def test_success_sends_success_notification(self, svc, show, torrent):
        episodes = [make_episode(1)]
        self._setup(svc, [make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=True)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        svc.notification_service.send_notification_to_all_providers.assert_called_once()
        title = svc.notification_service.send_notification_to_all_providers.call_args.kwargs[
            "title"
        ]
        assert title == "TV Show imported successfully"

    def test_failure_does_not_mark_torrent_imported(self, svc, show, torrent):
        episodes = [make_episode(1)]
        self._setup(svc, [make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=False)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        assert torrent.imported is False

    def test_failure_does_not_save_torrent(self, svc, show, torrent):
        episodes = [make_episode(1)]
        self._setup(svc, [make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=False)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        svc.torrent_service.torrent_repository.save_torrent.assert_not_called()

    def test_failure_sends_failure_notification(self, svc, show, torrent):
        episodes = [make_episode(1)]
        self._setup(svc, [make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=False)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        svc.notification_service.send_notification_to_all_providers.assert_called_once()
        title = svc.notification_service.send_notification_to_all_providers.call_args.kwargs[
            "title"
        ]
        assert title == "Failed to import TV Show"

    def test_multiple_episodes_all_succeed(self, svc, show, torrent):
        episodes = [make_episode(1), make_episode(2)]
        self._setup(svc, [make_season(1), make_season(1)], episodes)
        svc.import_episode_files = MagicMock(return_value=True)
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        assert torrent.imported is True

    def test_multiple_episodes_one_fails(self, svc, show, torrent):
        episodes = [make_episode(1), make_episode(2)]
        self._setup(svc, [make_season(1), make_season(1)], episodes)
        svc.import_episode_files = MagicMock(side_effect=[True, False])
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        assert torrent.imported is False

    def test_no_episode_files_returns_early(self, svc, show, torrent):
        svc.torrent_service.get_episode_files_of_torrent.return_value = []
        svc.import_episode_files_from_torrent(torrent=torrent, show=show)
        assert torrent.imported is False
        svc.torrent_service.torrent_repository.save_torrent.assert_not_called()
        svc.notification_service.send_notification_to_all_providers.assert_not_called()
