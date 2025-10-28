import uuid
from unittest.mock import MagicMock

import pytest

from media_manager.exceptions import NotFoundError
from media_manager.tv.schemas import Show, ShowId, SeasonId
from media_manager.tv.service import TvService
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.metadataProvider.schemas import MetaDataProviderSearchResult


@pytest.fixture
def mock_tv_repository():
    return MagicMock()


@pytest.fixture
def mock_torrent_service():
    return MagicMock()


@pytest.fixture
def mock_indexer_service():
    return MagicMock()


@pytest.fixture
def tv_service(mock_tv_repository, mock_torrent_service, mock_indexer_service):
    return TvService(
        tv_repository=mock_tv_repository,
        torrent_service=mock_torrent_service,
        indexer_service=mock_indexer_service,
    )


def test_add_show(tv_service, mock_tv_repository, mock_torrent_service):
    external_id = 123
    # Now we pass a mock metadata provider object
    mock_metadata_provider = MagicMock()
    show_data = Show(
        id=ShowId(uuid.uuid4()),
        name="Test Show",
        overview="Test Overview",
        year=2022,
        external_id=external_id,
        metadata_provider="tmdb",
        seasons=[],
    )
    mock_metadata_provider.get_show_metadata.return_value = show_data
    mock_metadata_provider.download_show_poster_image.return_value = True
    mock_tv_repository.save_show.return_value = show_data

    result = tv_service.add_show(
        external_id=external_id, metadata_provider=mock_metadata_provider
    )

    mock_metadata_provider.get_show_metadata.assert_called_once_with(id=external_id)
    mock_tv_repository.save_show.assert_called_once_with(show=show_data)
    mock_metadata_provider.download_show_poster_image.assert_called_once_with(
        show=show_data
    )
    assert result == show_data


def test_add_show_with_invalid_metadata(
    tv_service, mock_tv_repository, mock_torrent_service
):
    external_id = 123
    mock_metadata_provider = MagicMock()
    # Simulate metadata provider returning None
    mock_metadata_provider.get_show_metadata.return_value = None
    mock_metadata_provider.download_show_poster_image.return_value = False
    mock_tv_repository.save_show.return_value = None
    result = tv_service.add_show(
        external_id=external_id, metadata_provider=mock_metadata_provider
    )
    mock_metadata_provider.get_show_metadata.assert_called_once_with(id=external_id)
    assert result is None


def test_check_if_show_exists_by_external_id(
    tv_service, mock_tv_repository, mock_torrent_service
):
    external_id = 123
    metadata_provider = "tmdb"
    mock_tv_repository.get_show_by_external_id.return_value = "show_obj"
    assert tv_service.check_if_show_exists(
        external_id=external_id, metadata_provider=metadata_provider
    )
    mock_tv_repository.get_show_by_external_id.assert_called_once_with(
        external_id=external_id, metadata_provider=metadata_provider
    )

    mock_tv_repository.get_show_by_external_id.side_effect = NotFoundError
    assert not tv_service.check_if_show_exists(
        external_id=external_id, metadata_provider=metadata_provider
    )


def test_check_if_show_exists_by_show_id(
    tv_service, mock_tv_repository, mock_torrent_service
):
    show_id = ShowId(uuid.uuid4())
    mock_tv_repository.get_show_by_id.return_value = "show_obj"
    assert tv_service.check_if_show_exists(show_id=show_id)
    mock_tv_repository.get_show_by_id.assert_called_once_with(show_id=show_id)

    mock_tv_repository.get_show_by_id.side_effect = NotFoundError
    assert not tv_service.check_if_show_exists(show_id=show_id)


def test_check_if_show_exists_with_invalid_uuid(
    tv_service, mock_tv_repository, mock_torrent_service
):
    # Simulate NotFoundError for a random UUID
    show_id = ShowId(uuid.uuid4())
    mock_tv_repository.get_show_by_id.side_effect = NotFoundError
    assert not tv_service.check_if_show_exists(show_id=show_id)


def test_check_if_show_exists_raises_value_error(tv_service, mock_torrent_service):
    with pytest.raises(ValueError):
        tv_service.check_if_show_exists()


def test_add_season_request(tv_service, mock_tv_repository, mock_torrent_service):
    season_request = MagicMock()
    mock_tv_repository.add_season_request.return_value = season_request
    result = tv_service.add_season_request(season_request)
    mock_tv_repository.add_season_request.assert_called_once_with(
        season_request=season_request
    )
    assert result == season_request


def test_get_season_request_by_id(tv_service, mock_tv_repository, mock_torrent_service):
    season_request_id = MagicMock()
    season_request = MagicMock()
    mock_tv_repository.get_season_request.return_value = season_request
    result = tv_service.get_season_request_by_id(season_request_id)
    mock_tv_repository.get_season_request.assert_called_once_with(
        season_request_id=season_request_id
    )
    assert result == season_request


def test_update_season_request(tv_service, mock_tv_repository, mock_torrent_service):
    season_request = MagicMock()
    mock_tv_repository.add_season_request.return_value = season_request
    result = tv_service.update_season_request(season_request)
    mock_tv_repository.delete_season_request.assert_called_once_with(
        season_request_id=season_request.id
    )
    mock_tv_repository.add_season_request.assert_called_once_with(
        season_request=season_request
    )
    assert result == season_request


def test_delete_season_request(tv_service, mock_tv_repository, mock_torrent_service):
    season_request_id = MagicMock()
    tv_service.delete_season_request(season_request_id)
    mock_tv_repository.delete_season_request.assert_called_once_with(
        season_request_id=season_request_id
    )


def test_get_all_shows(tv_service, mock_tv_repository, mock_torrent_service):
    shows = [MagicMock(), MagicMock()]
    mock_tv_repository.get_shows.return_value = shows
    result = tv_service.get_all_shows()
    mock_tv_repository.get_shows.assert_called_once()
    assert result == shows


def test_get_show_by_id(tv_service, mock_tv_repository, mock_torrent_service):
    show_id = MagicMock()
    show = MagicMock()
    mock_tv_repository.get_show_by_id.return_value = show
    result = tv_service.get_show_by_id(show_id)
    mock_tv_repository.get_show_by_id.assert_called_once_with(show_id=show_id)
    assert result == show


def test_get_show_by_id_not_found(tv_service, mock_tv_repository, mock_torrent_service):
    show_id = ShowId(uuid.uuid4())
    mock_tv_repository.get_show_by_id.side_effect = NotFoundError
    try:
        tv_service.get_show_by_id(show_id)
    except NotFoundError:
        assert True
    else:
        assert False


def test_get_show_by_external_id(tv_service, mock_tv_repository, mock_torrent_service):
    external_id = 123
    metadata_provider = "tmdb"
    show = MagicMock()
    mock_tv_repository.get_show_by_external_id.return_value = show
    result = tv_service.get_show_by_external_id(external_id, metadata_provider)
    mock_tv_repository.get_show_by_external_id.assert_called_once_with(
        external_id=external_id, metadata_provider=metadata_provider
    )
    assert result == show


def test_get_show_by_external_id_not_found(
    tv_service, mock_tv_repository, mock_torrent_service
):
    external_id = 123
    metadata_provider = "tmdb"
    mock_tv_repository.get_show_by_external_id.side_effect = NotFoundError
    try:
        tv_service.get_show_by_external_id(external_id, metadata_provider)
    except NotFoundError:
        assert True
    else:
        assert False


def test_get_season(tv_service, mock_tv_repository, mock_torrent_service):
    season_id = MagicMock()
    season = MagicMock()
    mock_tv_repository.get_season.return_value = season
    result = tv_service.get_season(season_id)
    mock_tv_repository.get_season.assert_called_once_with(season_id=season_id)
    assert result == season


def test_get_season_not_found(tv_service, mock_tv_repository, mock_torrent_service):
    season_id = SeasonId(uuid.uuid4())
    mock_tv_repository.get_season.side_effect = NotFoundError
    try:
        tv_service.get_season(season_id)
    except NotFoundError:
        assert True
    else:
        assert False


def test_get_all_season_requests(tv_service, mock_tv_repository, mock_torrent_service):
    requests = [MagicMock(), MagicMock()]
    mock_tv_repository.get_season_requests.return_value = requests
    result = tv_service.get_all_season_requests()
    mock_tv_repository.get_season_requests.assert_called_once()
    assert result == requests


def test_get_public_season_files_by_season_id_downloaded(
    monkeypatch, tv_service, mock_tv_repository, mock_torrent_service
):
    season_id = MagicMock()
    season_file = MagicMock()
    public_season_file = MagicMock()
    public_season_file.downloaded = False
    mock_tv_repository.get_season_files_by_season_id.return_value = [season_file]
    monkeypatch.setattr(
        "media_manager.tv.schemas.PublicSeasonFile.model_validate",
        lambda x: public_season_file,
    )
    monkeypatch.setattr(
        tv_service, "season_file_exists_on_file", lambda season_file: True
    )
    result = tv_service.get_public_season_files_by_season_id(season_id)
    assert result[0].downloaded is True


def test_get_public_season_files_by_season_id_not_downloaded(
    monkeypatch, tv_service, mock_tv_repository, mock_torrent_service
):
    season_id = MagicMock()
    season_file = MagicMock()
    public_season_file = MagicMock()
    public_season_file.downloaded = False
    mock_tv_repository.get_season_files_by_season_id.return_value = [season_file]
    monkeypatch.setattr(
        "media_manager.tv.schemas.PublicSeasonFile.model_validate",
        lambda x: public_season_file,
    )
    monkeypatch.setattr(
        tv_service, "season_file_exists_on_file", lambda season_file: False
    )
    result = tv_service.get_public_season_files_by_season_id(season_id)
    assert result[0].downloaded is False


def test_get_public_season_files_by_season_id_empty(
    tv_service, mock_tv_repository, mock_torrent_service
):
    season_id = SeasonId(uuid.uuid4())
    mock_tv_repository.get_season_files_by_season_id.return_value = []
    result = tv_service.get_public_season_files_by_season_id(season_id)
    assert result == []


def test_is_season_downloaded_true(
    monkeypatch, tv_service, mock_tv_repository, mock_torrent_service
):
    season_id = MagicMock()
    season_file = MagicMock()
    mock_tv_repository.get_season_files_by_season_id.return_value = [season_file]
    monkeypatch.setattr(
        tv_service, "season_file_exists_on_file", lambda season_file: True
    )
    assert tv_service.is_season_downloaded(season_id) is True


def test_is_season_downloaded_false(
    monkeypatch, tv_service, mock_tv_repository, mock_torrent_service
):
    season_id = MagicMock()
    season_file = MagicMock()
    mock_tv_repository.get_season_files_by_season_id.return_value = [season_file]
    monkeypatch.setattr(
        tv_service, "season_file_exists_on_file", lambda season_file: False
    )
    assert tv_service.is_season_downloaded(season_id) is False


def test_is_season_downloaded_with_no_files(
    tv_service, mock_tv_repository, mock_torrent_service
):
    season_id = SeasonId(uuid.uuid4())
    mock_tv_repository.get_season_files_by_season_id.return_value = []
    assert tv_service.is_season_downloaded(season_id) is False


def test_season_file_exists_on_file_none(monkeypatch, tv_service, mock_torrent_service):
    season_file = MagicMock()
    season_file.torrent_id = None
    assert tv_service.season_file_exists_on_file(season_file) is True


def test_season_file_exists_on_file_imported(
    monkeypatch, tv_service, mock_torrent_service
):
    season_file = MagicMock()
    season_file.torrent_id = "torrent_id"
    torrent_file = MagicMock(imported=True)
    # Patch the repository method on the torrent_service instance
    tv_service.torrent_service.torrent_repository.get_torrent_by_id = MagicMock(
        return_value=torrent_file
    )
    assert tv_service.season_file_exists_on_file(season_file) is True


def test_season_file_exists_on_file_not_imported(
    monkeypatch, tv_service, mock_torrent_service
):
    season_file = MagicMock()
    season_file.torrent_id = "torrent_id"
    torrent_file = MagicMock()
    torrent_file.torrent_id = "torrent_id"
    torrent_file.imported = False
    tv_service.torrent_service.get_torrent_by_id = MagicMock(return_value=torrent_file)
    assert tv_service.season_file_exists_on_file(season_file) is False


def test_season_file_exists_on_file_with_none_imported(
    monkeypatch, tv_service, mock_torrent_service
):
    class DummySeasonFile:
        def __init__(self):
            self.torrent_id = uuid.uuid4()

    dummy_file = DummySeasonFile()

    class DummyTorrent:
        imported = True

    tv_service.torrent_service.torrent_repository.get_torrent_by_id = MagicMock(
        return_value=DummyTorrent()
    )
    assert tv_service.season_file_exists_on_file(dummy_file) is True


def test_season_file_exists_on_file_with_none_not_imported(
    monkeypatch, tv_service, mock_torrent_service
):
    class DummySeasonFile:
        def __init__(self):
            self.torrent_id = uuid.uuid4()

    dummy_file = DummySeasonFile()

    class DummyTorrent:
        imported = False

    tv_service.torrent_service.get_torrent_by_id = MagicMock(
        return_value=DummyTorrent()
    )
    assert tv_service.season_file_exists_on_file(dummy_file) is False


def test_get_all_available_torrents_for_a_season_with_override(
    tv_service, mock_tv_repository, mock_torrent_service, mock_indexer_service
):
    show_id = ShowId(uuid.uuid4())
    season_number = 1
    override_query = "Custom Query S01"
    mock_show = Show(
        id=show_id,
        name="Test Show",
        overview="",
        year=2020,
        external_id=1,
        metadata_provider="tmdb",
        seasons=[],
    )
    mock_tv_repository.get_show_by_id.return_value = mock_show

    torrent1 = IndexerQueryResult(
        id=IndexerQueryResultId(uuid.uuid4()),
        title="Custom Query S01E01",
        _download_url="https://example.com/torrent1",
        seeders=10,
        flags=[],
        size=100,
        usenet=False,
        age=1,
    )
    mock_indexer_service.search.return_value = [torrent1]

    results = tv_service.get_all_available_torrents_for_a_season(
        season_number=season_number,
        show_id=show_id,
        search_query_override=override_query,
    )

    mock_indexer_service.search.assert_called_once_with(
        query=override_query, is_tv=True
    )
    assert results == [torrent1]


def test_get_all_available_torrents_for_a_season_no_results(
    tv_service, mock_tv_repository, mock_torrent_service, mock_indexer_service
):
    show_id = ShowId(uuid.uuid4())
    season_number = 1
    mock_show = Show(
        id=show_id,
        name="Test Show",
        overview="",
        year=2020,
        external_id=1,
        metadata_provider="tmdb",
        seasons=[],
    )
    mock_tv_repository.get_show_by_id.return_value = mock_show

    mock_indexer_service.search.return_value = []

    results = tv_service.get_all_available_torrents_for_a_season(
        season_number=season_number, show_id=show_id
    )
    assert results == []


def test_search_for_show_no_existing(tv_service, mock_torrent_service):
    query = "Test Show"
    mock_metadata_provider = MagicMock()
    search_result_item = MetaDataProviderSearchResult(
        external_id=123,
        name="Test Show",
        year=2022,
        overview="Overview",
        metadata_provider="tmdb",
        added=False,
        poster_path=None,
    )
    mock_metadata_provider.search_show.return_value = [search_result_item]
    mock_metadata_provider.name = "tmdb"
    tv_service.check_if_show_exists = MagicMock(return_value=False)
    results = tv_service.search_for_show(
        query=query, metadata_provider=mock_metadata_provider
    )
    mock_metadata_provider.search_show.assert_called_once_with(query)
    assert len(results) == 1
    assert results[0] == search_result_item
    assert results[0].added is False


def test_search_for_show_with_existing(tv_service, mock_torrent_service):
    query = "Test Show"
    mock_metadata_provider = MagicMock()
    search_result_item = MetaDataProviderSearchResult(
        external_id=123,
        name="Test Show",
        year=2022,
        overview="Overview",
        metadata_provider="tmdb",
        added=False,
        poster_path=None,
    )
    mock_metadata_provider.search_show.return_value = [search_result_item]
    mock_metadata_provider.name = "tmdb"
    tv_service.check_if_show_exists = MagicMock(return_value=True)
    results = tv_service.search_for_show(
        query=query, metadata_provider=mock_metadata_provider
    )
    assert len(results) == 1
    assert results[0].added is True


def test_search_for_show_empty_results(tv_service, mock_torrent_service):
    query = "NonExistent Show"
    mock_metadata_provider = MagicMock()
    mock_metadata_provider.search_show.return_value = []
    tv_service.check_if_show_exists = MagicMock()
    results = tv_service.search_for_show(
        query=query, metadata_provider=mock_metadata_provider
    )
    assert results == []


def test_get_popular_shows_none_added(tv_service, mock_torrent_service):
    mock_metadata_provider = MagicMock()
    popular_show1 = MetaDataProviderSearchResult(
        external_id=123,
        name="Popular Show 1",
        year=2022,
        overview="Overview1",
        metadata_provider="tmdb",
        added=False,
        poster_path=None,
    )
    popular_show2 = MetaDataProviderSearchResult(
        external_id=456,
        name="Popular Show 2",
        year=2023,
        overview="Overview2",
        metadata_provider="tmdb",
        added=False,
        poster_path=None,
    )
    mock_metadata_provider.search_show.return_value = [popular_show1, popular_show2]
    mock_metadata_provider.name = "tmdb"
    tv_service.check_if_show_exists = MagicMock(return_value=False)
    results = tv_service.get_popular_shows(metadata_provider=mock_metadata_provider)
    assert len(results) == 2
    assert popular_show1 in results
    assert popular_show2 in results


def test_get_popular_shows_all_added(tv_service, mock_torrent_service):
    mock_metadata_provider = MagicMock()
    popular_show1 = MetaDataProviderSearchResult(
        external_id=123,
        name="Popular Show 1",
        year=2022,
        overview="Overview1",
        metadata_provider="tmdb",
        added=False,
        poster_path=None,
    )
    mock_metadata_provider.search_show.return_value = [popular_show1]
    mock_metadata_provider.name = "tmdb"
    tv_service.check_if_show_exists = MagicMock(return_value=True)
    results = tv_service.get_popular_shows(metadata_provider=mock_metadata_provider)
    assert results == []


def test_get_popular_shows_empty_from_provider(tv_service, mock_torrent_service):
    mock_metadata_provider = MagicMock()
    mock_metadata_provider.search_show.return_value = []
    tv_service.check_if_show_exists = MagicMock()
    results = tv_service.get_popular_shows(metadata_provider=mock_metadata_provider)
    assert results == []
