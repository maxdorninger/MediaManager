import pytest

from media_manager.indexer.schemas import IndexerQueryResult

DEFAULTS = dict(
    download_url="magnet:?xt=test",
    seeders=10,
    flags=[],
    size=1000,
    usenet=False,
    age=0,
    indexer="test",
)


def season(title: str) -> list[int]:
    return IndexerQueryResult(title=title, **DEFAULTS).season


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Show S01 (2020) 1080p", [1]),
        ("Show S03 720p", [3]),
        ("The Lol-Files (1996) S01-S11 1080p", list(range(1, 12))),
        ("Brooklyn One-Two (2010) S01-9 S01-S09 1080p", list(range(1, 10))),
        ("Some Show S01-8 720p", list(range(1, 9))),
        ("Nurses (2001) Complete 1080p", []),  # reject
        ("The Midnight Zone 1959 Seasons 1 to 5 720p", []),  # reject
    ],
)
def test_season_parser(title, expected):
    assert season(title) == expected
