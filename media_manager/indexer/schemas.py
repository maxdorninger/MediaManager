import re
import typing
from uuid import UUID, uuid4

import pydantic
from pydantic import BaseModel, ConfigDict, computed_field

from media_manager.torrent.models import Quality

IndexerQueryResultId = typing.NewType("IndexerQueryResultId", UUID)


class IndexerQueryResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: IndexerQueryResultId = pydantic.Field(
        default_factory=lambda: IndexerQueryResultId(uuid4())
    )
    title: str
    download_url: str = pydantic.Field(
        exclude=True,
        description="This can be a magnet link or URL to the .torrent file",
    )
    seeders: int
    flags: list[str]
    size: int

    usenet: bool
    age: int

    score: int = 0

    indexer: str | None

    @computed_field
    @property
    def quality(self) -> Quality:
        high_quality_pattern = r"\b(4k)\b"
        medium_quality_pattern = r"\b(1080p)\b"
        low_quality_pattern = r"\b(720p)\b"
        very_low_quality_pattern = r"\b(480p|360p)\b"

        if re.search(high_quality_pattern, self.title, re.IGNORECASE):
            return Quality.uhd
        if re.search(medium_quality_pattern, self.title, re.IGNORECASE):
            return Quality.fullhd
        if re.search(low_quality_pattern, self.title, re.IGNORECASE):
            return Quality.hd
        if re.search(very_low_quality_pattern, self.title, re.IGNORECASE):
            return Quality.sd

        return Quality.unknown

    @computed_field
    @property
    def season(self) -> list[int]:
        # Try explicit range: S01-S08
        range_match = re.search(r"\bS(\d+)\s*-\s*S(\d+)\b", self.title, re.IGNORECASE)
        if range_match:
            return list(range(int(range_match.group(1)), int(range_match.group(2)) + 1))

        # Try shorthand range: S01-8 (S prefix only on first)
        shorthand_match = re.search(
            r"\bS(\d+)\s*-\s*(\d+)\b", self.title, re.IGNORECASE
        )
        if shorthand_match:
            start, end = int(shorthand_match.group(1)), int(shorthand_match.group(2))
            if end > start:
                return list(range(start, end + 1))

        # Fall back to individual S## matches, deduplicated
        pattern = r"\bS(\d+)\b"
        matches = re.findall(pattern, self.title, re.IGNORECASE)
        if matches:
            return sorted(set(int(m) for m in matches))

        return []

    def __gt__(self, other: "IndexerQueryResult") -> bool:
        if self.quality.value != other.quality.value:
            return self.quality.value < other.quality.value
        if self.score != other.score:
            return self.score > other.score
        if self.usenet != other.usenet:
            return self.usenet
        if self.usenet and other.usenet:
            return self.age > other.age
        if not self.usenet and not other.usenet:
            return self.seeders > other.seeders

        return self.size < other.size

    def __lt__(self, other: "IndexerQueryResult") -> bool:
        if self.quality.value != other.quality.value:
            return self.quality.value > other.quality.value
        if self.score != other.score:
            return self.score < other.score
        if self.usenet != other.usenet:
            return not self.usenet
        if self.usenet and other.usenet:
            return self.age < other.age
        if not self.usenet and not other.usenet:
            return self.seeders < other.seeders

        return self.size > other.size
