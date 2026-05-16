from typing import Any

from media_manager.indexer.schemas import IndexerQueryResult


def make_indexer_result(**overrides: Any) -> IndexerQueryResult:
    """Build an IndexerQueryResult with sensible defaults.

    Pass kwargs to override individual fields.
    """
    defaults: dict[str, Any] = {
        "title": "Some.Show.S01E01.1080p.WEB-DL.x265-RELEASE",
        "download_url": "magnet:?xt=urn:btih:0000000000000000000000000000000000000000",
        "seeders": 10,
        "flags": [],
        "size": 1_500_000_000,
        "usenet": False,
        "age": 0,
        "indexer": "test",
    }
    return IndexerQueryResult(**{**defaults, **overrides})
