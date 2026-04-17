from unittest.mock import MagicMock, patch

import pytest

from media_manager.torrent.download_clients.nzbget import NzbgetDownloadClient
from media_manager.torrent.schemas import Quality, Torrent, TorrentStatus


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.host = "localhost"
    config.port = 6789
    config.username = "nzbget"
    config.password = "tegbzn6789"
    config.use_https = False
    return config


@pytest.fixture
def nzbget_client(mock_config):
    with (
        patch(
            "media_manager.torrent.download_clients.nzbget.MediaManagerConfig"
        ) as mock_mm_config,
        patch("media_manager.torrent.download_clients.nzbget.requests") as mock_requests,
    ):
        mock_mm_config.return_value.torrents.nzbget = mock_config
        # Mock the version call during __init__
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "21.1", "id": 1}
        mock_response.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_response

        client = NzbgetDownloadClient()
        # Replace requests reference so subsequent calls can be mocked cleanly
        client._requests = mock_requests
        return client


class TestNzbgetStatusMapping:
    def test_downloading_states(self, nzbget_client):
        downloading_states = [
            "QUEUED",
            "PAUSED",
            "DOWNLOADING",
            "FETCHING",
            "PP_QUEUED",
            "LOADING_PARS",
            "VERIFYING_SOURCES",
            "REPAIRING",
            "VERIFYING_REPAIRED",
            "RENAMING",
            "UNPACKING",
            "MOVING",
            "EXECUTING_SCRIPT",
        ]
        for state in downloading_states:
            assert nzbget_client._map_status(state) == TorrentStatus.downloading

    def test_finished_state(self, nzbget_client):
        assert nzbget_client._map_status("SUCCESS") == TorrentStatus.finished

    def test_error_state(self, nzbget_client):
        assert nzbget_client._map_status("FAILURE") == TorrentStatus.error

    def test_unknown_state(self, nzbget_client):
        assert nzbget_client._map_status("SOMETHING_ELSE") == TorrentStatus.unknown


class TestNzbgetDownloadClient:
    def test_init_builds_correct_url(self, mock_config):
        with (
            patch(
                "media_manager.torrent.download_clients.nzbget.MediaManagerConfig"
            ) as mock_mm_config,
            patch(
                "media_manager.torrent.download_clients.nzbget.requests"
            ) as mock_requests,
        ):
            mock_mm_config.return_value.torrents.nzbget = mock_config
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": "21.1", "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            client = NzbgetDownloadClient()

            assert client._base_url == "http://localhost:6789"
            assert client._auth == ("nzbget", "tegbzn6789")

    def test_init_https(self, mock_config):
        mock_config.use_https = True
        with (
            patch(
                "media_manager.torrent.download_clients.nzbget.MediaManagerConfig"
            ) as mock_mm_config,
            patch(
                "media_manager.torrent.download_clients.nzbget.requests"
            ) as mock_requests,
        ):
            mock_mm_config.return_value.torrents.nzbget = mock_config
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": "21.1", "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            client = NzbgetDownloadClient()

            assert client._base_url == "https://localhost:6789"

    def test_init_connection_failure(self, mock_config):
        with (
            patch(
                "media_manager.torrent.download_clients.nzbget.MediaManagerConfig"
            ) as mock_mm_config,
            patch(
                "media_manager.torrent.download_clients.nzbget.requests"
            ) as mock_requests,
        ):
            mock_mm_config.return_value.torrents.nzbget = mock_config
            mock_requests.post.side_effect = ConnectionError("Connection refused")

            with pytest.raises(ConnectionError):
                NzbgetDownloadClient()

    def test_call_api_error(self, nzbget_client):
        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "error": {"name": "Error", "message": "Bad request"},
                "id": 1,
            }
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            with pytest.raises(RuntimeError, match="NZBGet API error"):
                nzbget_client._call("badmethod")

    def test_download_torrent(self, nzbget_client):
        indexer_result = MagicMock()
        indexer_result.title = "Test.Show.S01E01.720p"
        indexer_result.download_url = "http://example.com/test.nzb"
        indexer_result.quality = Quality.hd

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            # First call: append returns NZB ID
            # Second call: listgroups for status check
            append_response = MagicMock()
            append_response.json.return_value = {"result": 12345, "id": 1}
            append_response.raise_for_status = MagicMock()

            status_response = MagicMock()
            status_response.json.return_value = {
                "result": [{"NZBID": 12345, "Status": "QUEUED"}],
                "id": 1,
            }
            status_response.raise_for_status = MagicMock()

            mock_requests.post.side_effect = [append_response, status_response]

            torrent = nzbget_client.download_torrent(indexer_result)

            assert torrent.hash == "12345"
            assert torrent.title == "Test.Show.S01E01.720p"
            assert torrent.usenet is True
            assert torrent.status == TorrentStatus.downloading

    def test_download_torrent_failure(self, nzbget_client):
        indexer_result = MagicMock()
        indexer_result.title = "Test.Show.S01E01.720p"
        indexer_result.download_url = "http://example.com/test.nzb"

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            fail_response = MagicMock()
            fail_response.json.return_value = {"result": -1, "id": 1}
            fail_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = fail_response

            with pytest.raises(RuntimeError, match="Failed to add NZB"):
                nzbget_client.download_torrent(indexer_result)

    def test_remove_torrent(self, nzbget_client):
        torrent = Torrent(
            status=TorrentStatus.downloading,
            title="Test",
            quality=Quality.hd,
            imported=False,
            hash="12345",
            usenet=True,
        )

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": True, "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            nzbget_client.remove_torrent(torrent)

            call_args = mock_requests.post.call_args
            payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
            assert payload["method"] == "editqueue"

    def test_pause_torrent(self, nzbget_client):
        torrent = Torrent(
            status=TorrentStatus.downloading,
            title="Test",
            quality=Quality.hd,
            imported=False,
            hash="12345",
            usenet=True,
        )

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": True, "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            nzbget_client.pause_torrent(torrent)

            call_args = mock_requests.post.call_args
            payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
            assert payload["method"] == "editqueue"
            assert payload["params"][0] == "GroupPause"

    def test_resume_torrent(self, nzbget_client):
        torrent = Torrent(
            status=TorrentStatus.downloading,
            title="Test",
            quality=Quality.hd,
            imported=False,
            hash="12345",
            usenet=True,
        )

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": True, "id": 1}
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            nzbget_client.resume_torrent(torrent)

            call_args = mock_requests.post.call_args
            payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
            assert payload["method"] == "editqueue"
            assert payload["params"][0] == "GroupResume"

    def test_get_torrent_status_from_queue(self, nzbget_client):
        torrent = Torrent(
            status=TorrentStatus.unknown,
            title="Test",
            quality=Quality.hd,
            imported=False,
            hash="12345",
            usenet=True,
        )

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "result": [{"NZBID": 12345, "Status": "DOWNLOADING"}],
                "id": 1,
            }
            mock_response.raise_for_status = MagicMock()
            mock_requests.post.return_value = mock_response

            status = nzbget_client.get_torrent_status(torrent)
            assert status == TorrentStatus.downloading

    def test_get_torrent_status_from_history(self, nzbget_client):
        torrent = Torrent(
            status=TorrentStatus.unknown,
            title="Test",
            quality=Quality.hd,
            imported=False,
            hash="12345",
            usenet=True,
        )

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            # First call: listgroups returns empty
            queue_response = MagicMock()
            queue_response.json.return_value = {"result": [], "id": 1}
            queue_response.raise_for_status = MagicMock()

            # Second call: history returns completed item
            history_response = MagicMock()
            history_response.json.return_value = {
                "result": [{"NZBID": 12345, "Status": "SUCCESS"}],
                "id": 1,
            }
            history_response.raise_for_status = MagicMock()

            mock_requests.post.side_effect = [queue_response, history_response]

            status = nzbget_client.get_torrent_status(torrent)
            assert status == TorrentStatus.finished

    def test_get_torrent_status_not_found(self, nzbget_client):
        torrent = Torrent(
            status=TorrentStatus.unknown,
            title="Test",
            quality=Quality.hd,
            imported=False,
            hash="99999",
            usenet=True,
        )

        with patch(
            "media_manager.torrent.download_clients.nzbget.requests"
        ) as mock_requests:
            empty_response = MagicMock()
            empty_response.json.return_value = {"result": [], "id": 1}
            empty_response.raise_for_status = MagicMock()

            mock_requests.post.return_value = empty_response

            status = nzbget_client.get_torrent_status(torrent)
            assert status == TorrentStatus.unknown
