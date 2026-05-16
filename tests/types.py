from typing import Protocol

from media_manager.indexer.config import (
    IndexerFlagScoringRule,
    TitleScoringRule,
)


class PatchScoringRules(Protocol):
    """Signature of the `patch_scoring_rules` fixture."""

    def __call__(
        self,
        title: list[TitleScoringRule] | None = None,
        flags: list[IndexerFlagScoringRule] | None = None,
    ) -> None: ...
