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
        high_quality_pattern = r"\b(4k|2160p|uhd)\b"
        medium_quality_pattern = r"\b(1080p|full[ ._-]?hd)\b"
        low_quality_pattern = r"\b(720p|(?<!full[ ._-])hd(?![a-z]))\b"
        very_low_quality_pattern = r"\b(480p|360p|sd)\b"

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
        title = self.title.lower()

        # 1) S01E01 / S1E2
        m = re.search(r"s(\d{1,2})e\d{1,3}", title)
        if m:
            return [int(m.group(1))]

        # 2) Range S01-S03 / S1-S3
        m = re.search(r"s(\d{1,2})\s*(?:-|\u2013)\s*s?(\d{1,2})", title)
        if m:
            start, end = int(m.group(1)), int(m.group(2))
            if start <= end:
                return list(range(start, end + 1))
            return []

        # 3) Pack S01 / S1
        m = re.search(r"\bs(\d{1,2})\b", title)
        if m:
            return [int(m.group(1))]

        # 4) Season 01 / Season 1
        m = re.search(r"\bseason\s*(\d{1,2})\b", title)
        if m:
            return [int(m.group(1))]

        return []

    @computed_field(return_type=list[int])
    @property
    def episode(self) -> list[int]:
        title = self.title.lower()
        result: list[int] = []

        pattern = r"s\d{1,2}e(\d{1,3})(?:\s*-\s*(?:s?\d{1,2}e)?(\d{1,3}))?"
        match = re.search(pattern, title)

        if not match:
            return result

        start = int(match.group(1))
        end = match.group(2)

        if end:
            end = int(end)
            if end >= start:
                result = list(range(start, end + 1))
        else:
            result = [start]

        return result

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
