import pytest

from media_manager.torrent.schemas import Quality
from tests.factories.indexer import make_indexer_result


class TestQuality:
    @pytest.mark.parametrize(
        "title_prefix",
        ["Show Title.S01E01", "Movie Title"],
    )
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            (".2160p.WEB-DL", Quality.uhd),
            (".4K.WEB-DL", Quality.uhd),
            (".1080p.WEB-DL", Quality.fullhd),
            (".Full-HD.WEB-DL", Quality.fullhd),
            (".720p.WEB-DL", Quality.hd),
            (".480p.WEB-DL", Quality.sd),
            (".WEB-DL", Quality.unknown),
        ],
    )
    def test_quality_inferred_from_title(
        self, title_prefix: str, title: str, expected: Quality
    ) -> None:
        result = make_indexer_result(title=title_prefix + title)
        assert result.quality == expected


class TestSeason:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Show.S01E01", [1]),
            ("Show.S03E12.1080p", [3]),
            ("Show.S01-S03.Complete", [1, 2, 3]),
            ("Show Season 2 1080p", [2]),
            ("Show.S05.Complete", [5]),
            ("Show.Random.Title", []),
        ],
    )
    def test_season_extraction(self, title: str, expected: list[int]) -> None:
        assert make_indexer_result(title=title).season == expected


class TestEpisode:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Show.S01E01", [1]),
            ("Show.S01E01-S01E03", [1, 2, 3]),
            ("Show.S01E05-07", [5, 6, 7]),
            ("Show.S01.Complete", []),
        ],
    )
    def test_episode_extraction(self, title: str, expected: list[int]) -> None:
        assert make_indexer_result(title=title).episode == expected


class TestOrdering:
    def test_higher_quality_sorts_first(self) -> None:
        # __gt__ on IndexerQueryResult means "better than"; sorting in
        # descending order puts the best result first.
        uhd = make_indexer_result(title="SomeName.S01E01.2160p")
        hd = make_indexer_result(title="SomeName.S01E01.1080p")
        sd = make_indexer_result(title="SomeName.S01E01.480p")
        ordered = sorted([sd, uhd, hd], reverse=True)
        assert [r.quality for r in ordered] == [Quality.uhd, Quality.fullhd, Quality.sd]

    def test_same_quality_higher_score_first(self) -> None:
        a = make_indexer_result(title="SomeName.S01E01.1080p", score=100)
        b = make_indexer_result(title="OtherName.S01E01.1080p", score=50)
        assert sorted([b, a], reverse=True)[0].score == 100

    def test_same_quality_and_score_higher_seeders_first(self) -> None:
        a = make_indexer_result(title="SomeName.S01E01.1080p", seeders=200)
        b = make_indexer_result(title="OtherName.S01E01.1080p", seeders=10)
        assert sorted([b, a], reverse=True)[0].seeders == 200
