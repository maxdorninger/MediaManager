import uuid
from unittest.mock import MagicMock, patch
import pytest

from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.indexer.repository import IndexerRepository
from media_manager.indexer.service import IndexerService
from media_manager.indexer.indexers.generic import GenericIndexer


class DummyIndexer(GenericIndexer):
    def __init__(self):
        super().__init__(name="DummyIndexer")

    def search(self, query, is_tv=True):
        return [
            IndexerQueryResult(
                id=IndexerQueryResultId(uuid.uuid4()),
                title=f"{query} S01 1080p",
                _download_url="https://example.com/torrent1",
                seeders=10,
                flags=["test"],
                size=123456,
                usenet=False,
                age=1,
            )
        ]


@pytest.fixture
def mock_indexer_repository():
    repo = MagicMock(spec=IndexerRepository)
    repo.save_result.side_effect = lambda result: result
    return repo


@pytest.fixture
def indexer_service(mock_indexer_repository):
    # Mock the config to disable real indexers
    with patch("media_manager.indexer.service.AllEncompassingConfig") as mock_config:
        # Configure the mock to disable all real indexers
        mock_config.return_value.indexers.prowlarr.enabled = False
        mock_config.return_value.indexers.jackett.enabled = False

        service = IndexerService(indexer_repository=mock_indexer_repository)
        # Manually set the dummy indexer
        service.indexers = [DummyIndexer()]
        return service


def test_search_returns_results(indexer_service, mock_indexer_repository):
    query = "TestShow"
    results = indexer_service.search(query, is_tv=True)
    assert len(results) == 1
    assert results[0].title == f"{query} S01 1080p"
    mock_indexer_repository.save_result.assert_called_once()


def test_get_result_returns_result(mock_indexer_repository):
    result_id = IndexerQueryResultId(uuid.uuid4())
    expected_result = IndexerQueryResult(
        id=result_id,
        title="Test S01 1080p",
        _download_url="https://example.com/torrent2",
        seeders=10,
        flags=["test"],
        size=123456,
        usenet=False,
        age=1,
    )
    mock_indexer_repository.get_result.return_value = expected_result
    service = IndexerService(indexer_repository=mock_indexer_repository)
    result = service.get_result(result_id)
    assert result == expected_result
    mock_indexer_repository.get_result.assert_called_once_with(result_id=result_id)
