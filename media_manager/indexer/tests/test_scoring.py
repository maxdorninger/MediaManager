from media_manager.indexer.config import (
    IndexerFlagScoringRule,
    ScoringRuleSet,
    TitleScoringRule,
)
from media_manager.indexer.utils import evaluate_indexer_query_result
from tests.factories.indexer import make_indexer_result
from tests.types import PatchScoringRules


class TestEvaluateIndexerQueryResult:
    def test_title_keyword_match_adds_score(
        self, patch_scoring_rules: PatchScoringRules
    ) -> None:
        patch_scoring_rules(
            title=[
                TitleScoringRule(
                    name="prefer_h265",
                    keywords=["h265", "x265"],
                    score_modifier=100,
                ),
            ],
        )
        result = make_indexer_result(title="Show.S01E01.1080p.x265-RELEASE", score=0)
        ruleset = ScoringRuleSet(name="rs", rule_names=["prefer_h265"])

        scored, passed = evaluate_indexer_query_result(result, ruleset)

        assert scored.score == 100
        assert passed is True

    def test_title_keyword_miss_leaves_score_alone(
        self, patch_scoring_rules: PatchScoringRules
    ) -> None:
        patch_scoring_rules(
            title=[
                TitleScoringRule(
                    name="prefer_h265",
                    keywords=["h265"],
                    score_modifier=100,
                ),
            ],
        )
        result = make_indexer_result(title="Show.S01E01.1080p.x264-RELEASE", score=0)
        ruleset = ScoringRuleSet(name="rs", rule_names=["prefer_h265"])

        scored, passed = evaluate_indexer_query_result(result, ruleset)

        # Score stays at 0 — evaluate_indexer_query_result returns
        # passed=False when score <= 0.
        assert scored.score == 0
        assert passed is False

    def test_negate_rule_fires_when_keyword_absent(
        self, patch_scoring_rules: PatchScoringRules
    ) -> None:
        patch_scoring_rules(
            title=[
                TitleScoringRule(
                    name="require_freeleech_word",
                    keywords=["freeleech"],
                    score_modifier=-10_000,
                    negate=True,
                ),
            ],
        )
        result = make_indexer_result(title="Show.S01E01.1080p", score=50)
        ruleset = ScoringRuleSet(name="rs", rule_names=["require_freeleech_word"])

        scored, passed = evaluate_indexer_query_result(result, ruleset)

        assert scored.score == 50 - 10_000
        assert passed is False

    def test_word_boundary_prevents_substring_match(
        self, patch_scoring_rules: PatchScoringRules
    ) -> None:
        # "ts" must not match "torrents"; this is the exact regression the
        # \b boundaries in evaluate_indexer_query_result are there to prevent.
        patch_scoring_rules(
            title=[
                TitleScoringRule(
                    name="avoid_ts",
                    keywords=["ts"],
                    score_modifier=-10_000,
                ),
            ],
        )
        result = make_indexer_result(title="Show.S01E01.from.torrents.1080p", score=100)
        ruleset = ScoringRuleSet(name="rs", rule_names=["avoid_ts"])

        scored, _ = evaluate_indexer_query_result(result, ruleset)
        assert scored.score == 100

    def test_indexer_flag_rule_match_subtracts_score(
        self, patch_scoring_rules: PatchScoringRules
    ) -> None:
        patch_scoring_rules(
            flags=[
                IndexerFlagScoringRule(
                    name="reject_nuked",
                    flags=["nuked"],
                    score_modifier=-10_000,
                ),
            ],
        )
        result = make_indexer_result(
            title="Show.S01E01.1080p", flags=["nuked"], score=200
        )
        ruleset = ScoringRuleSet(name="rs", rule_names=["reject_nuked"])

        scored, passed = evaluate_indexer_query_result(result, ruleset)

        assert scored.score == 200 - 10_000
        assert passed is False

    def test_unknown_rule_name_is_ignored(
        self, patch_scoring_rules: PatchScoringRules
    ) -> None:
        patch_scoring_rules(
            title=[
                TitleScoringRule(
                    name="prefer_h265", keywords=["h265"], score_modifier=100
                ),
            ],
        )
        result = make_indexer_result(title="Show.S01E01.x265", score=10)
        ruleset = ScoringRuleSet(name="rs", rule_names=["does_not_exist"])

        scored, passed = evaluate_indexer_query_result(result, ruleset)

        assert scored.score == 10
        assert passed is True
