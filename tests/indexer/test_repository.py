import uuid
import pytest
from media_manager.indexer.schemas import IndexerQueryResult, IndexerQueryResultId
from media_manager.indexer.repository import IndexerRepository


class DummyDB:
    def __init__(self):
        self._storage = {}
        self.added = []
        self.committed = False

    def get(self, model, result_id):
        return self._storage.get(result_id)

    def add(self, obj):
        self.added.append(obj)
        self._storage[obj.id] = obj

    def commit(self):
        self.committed = True


@pytest.fixture
def dummy_db():
    return DummyDB()


@pytest.fixture
def repo(dummy_db):
    return IndexerRepository(db=dummy_db)


def test_save_and_get_result(repo, dummy_db):
    result_id = IndexerQueryResultId(uuid.uuid4())
    result = IndexerQueryResult(
        id=result_id,
        title="Test Title",
        _download_url="https://example.com/test1",
        seeders=5,
        flags=["flag1"],
        size=1234,
        usenet=False,
        age=1,
    )
    saved = repo.save_result(result)
    assert saved == result
    assert dummy_db.committed
    fetched = repo.get_result(result_id)
    assert fetched.id == result_id
    assert fetched.title == "Test Title"


def test_save_result_calls_db_methods(repo, dummy_db):
    result = IndexerQueryResult(
        id=IndexerQueryResultId(uuid.uuid4()),
        title="Another Title",
        _download_url="https://example.com/test2",
        seeders=2,
        flags=[],
        size=5678,
        usenet=False,
        age=1,
    )
    repo.save_result(result)
    assert dummy_db.added[0].title == "Another Title"
    assert dummy_db.committed
