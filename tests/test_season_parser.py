import pytest

from media_manager.indexer.schemas import IndexerQueryResult

DEFAULTS = {
    "download_url": "magnet:?xt=test",
    "seeders": 10,
    "flags": [],
    "size": 1000,
    "usenet": False,
    "age": 0,
    "indexer": "test",
}


def season(title: str) -> list[int]:
    return IndexerQueryResult(title=title, **DEFAULTS).season


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        # Single season pack
        ("Show S01 (2020) 1080p", [1]),
        ("Show S03 720p", [3]),
        # Season N pattern
        ("Show Season 3 720p", [3]),
        # Ranges
        ("The Lol-Files (1996) S01-S11 1080p", list(range(1, 12))),
        ("Brooklyn One-Two (2010) S01-9 S01-S09 1080p", list(range(1, 10))),
        ("Some Show S01-8 720p", list(range(1, 9))),
        ("Show S01\u2013S05 720p", list(range(1, 6))),  # em-dash range
        # Reversed ranges — rejected
        ("Show S05-3 720p", []),  # shorthand, no S prefix on end
        ("Show S05-S03 720p", []),  # explicit S prefix on both
        # Episode number present — season still extracted
        ("Show S01E05 720p", [1]),
        # Multiple individual seasons
        ("Show S01 S03 S05 720p", [1, 3, 5]),
        # No season identifiers — rejected
        ("Nurses (2001) Complete 1080p", []),
        ("The Midnight Zone 1959 Seasons 1 to 5 720p", []),
        # Multi-language word form (Sonarr parity)
        ("Show Saison 2 720p", [2]),  # French
        ("Show Series 4 1080p", [4]),  # English alternative
        ("Show Stagione 5 720p", [5]),  # Italian
        ("Show saison 2 720p", [2]),  # case-insensitive
    ],
)
def test_season_parser(title, expected):
    assert season(title) == expected
