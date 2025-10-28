from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.models import Quality


def test_quality_computed_field():
    assert (
        IndexerQueryResult(
            title="Show S01 4K",
            _download_url="https://example.com/1",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.uhd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 1080p",
            _download_url="https://example.com/2",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.fullhd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 720p",
            _download_url="https://example.com/3",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.hd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 480p",
            _download_url="https://example.com/4",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.sd
    )
    assert (
        IndexerQueryResult(
            title="Show S01",
            _download_url="https://example.com/5",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.unknown
    )


def test_quality_computed_field_edge_cases():
    # Case-insensitive
    assert (
        IndexerQueryResult(
            title="Show S01 4k",
            _download_url="https://example.com/6",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.uhd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 1080P",
            _download_url="https://example.com/7",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.fullhd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 720P",
            _download_url="https://example.com/8",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.hd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 480P",
            _download_url="https://example.com/9",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.sd
    )
    # Multiple quality tags, prefer highest
    assert (
        IndexerQueryResult(
            title="Show S01 4K 1080p 720p",
            _download_url="https://example.com/10",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.uhd
    )
    assert (
        IndexerQueryResult(
            title="Show S01 1080p 720p",
            _download_url="https://example.com/11",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.fullhd
    )
    # No quality tag
    assert (
        IndexerQueryResult(
            title="Show S01",
            _download_url="https://example.com/12",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.unknown
    )
    # Quality tag in the middle
    assert (
        IndexerQueryResult(
            title="4K Show S01",
            _download_url="https://example.com/13",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).quality
        == Quality.uhd
    )


def test_season_computed_field():
    # Single season
    assert IndexerQueryResult(
        title="Show S01",
        _download_url="https://example.com/14",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [1]
    # Range of seasons
    assert IndexerQueryResult(
        title="Show S01 S03",
        _download_url="https://example.com/15",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [1, 2, 3]
    # No season
    assert (
        IndexerQueryResult(
            title="Show",
            _download_url="https://example.com/16",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).season
        == []
    )


def test_season_computed_field_edge_cases():
    # Multiple seasons, unordered
    assert (
        IndexerQueryResult(
            title="Show S03 S01",
            _download_url="https://example.com/17",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).season
        == []
    )
    # Season with leading zeros
    assert IndexerQueryResult(
        title="Show S01 S03",
        _download_url="https://example.com/18",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [1, 2, 3]
    assert IndexerQueryResult(
        title="Show S01 S01",
        _download_url="https://example.com/19",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [1]
    # No season at all
    assert (
        IndexerQueryResult(
            title="Show",
            _download_url="https://example.com/20",
            seeders=1,
            flags=[],
            size=1,
            usenet=False,
            age=1,
        ).season
        == []
    )
    # Season in lower/upper case
    assert IndexerQueryResult(
        title="Show s02",
        _download_url="https://example.com/21",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [2]
    assert IndexerQueryResult(
        title="Show S02",
        _download_url="https://example.com/22",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [2]
    # Season with extra text
    assert IndexerQueryResult(
        title="Show S01 Complete",
        _download_url="https://example.com/23",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    ).season == [1]


def test_gt_and_lt_methods():
    a = IndexerQueryResult(
        title="Show S01 1080p",
        _download_url="https://example.com/24",
        seeders=5,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    b = IndexerQueryResult(
        title="Show S01 720p",
        _download_url="https://example.com/25",
        seeders=10,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    c = IndexerQueryResult(
        title="Show S01 1080p",
        _download_url="https://example.com/26",
        seeders=2,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    # a (fullhd) > b (hd)
    assert a > b
    assert not (b > a)
    # If quality is equal, compare by seeders (lower seeders is less than higher seeders)
    assert c < a
    assert a > c
    # If quality is equal, but seeders are equal, neither is greater
    d = IndexerQueryResult(
        title="Show S01 1080p",
        _download_url="https://example.com/27",
        seeders=5,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    assert not (a < d)
    assert not (a > d)


def test_gt_and_lt_methods_edge_cases():
    # Different qualities
    a = IndexerQueryResult(
        title="Show S01 4K",
        _download_url="https://example.com/28",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    b = IndexerQueryResult(
        title="Show S01 1080p",
        _download_url="https://example.com/29",
        seeders=100,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    assert a > b
    assert not (b > a)
    # Same quality, different seeders
    c = IndexerQueryResult(
        title="Show S01 4K",
        _download_url="https://example.com/30",
        seeders=2,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    assert a < c
    assert c > a
    # Same quality and seeders
    d = IndexerQueryResult(
        title="Show S01 4K",
        _download_url="https://example.com/31",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    assert not (a < d)
    assert not (a > d)
    # Unknown quality, should compare by seeders
    e = IndexerQueryResult(
        title="Show S01",
        _download_url="https://example.com/32",
        seeders=5,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    f = IndexerQueryResult(
        title="Show S01",
        _download_url="https://example.com/33",
        seeders=10,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    assert e < f
    assert f > e
    # Mixed known and unknown quality
    g = IndexerQueryResult(
        title="Show S01 720p",
        _download_url="https://example.com/34",
        seeders=1,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    h = IndexerQueryResult(
        title="Show S01",
        _download_url="https://example.com/35",
        seeders=100,
        flags=[],
        size=1,
        usenet=False,
        age=1,
    )
    assert g > h
    assert not (h > g)
