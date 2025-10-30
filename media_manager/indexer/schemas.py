import re
import typing
from uuid import UUID, uuid4

import pydantic
from pydantic import BaseModel, computed_field, ConfigDict

from media_manager.torrent.models import Quality

IndexerQueryResultId = typing.NewType("IndexerQueryResultId", UUID)


class IndexerQueryResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: IndexerQueryResultId = pydantic.Field(default_factory=uuid4)
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

    @computed_field(return_type=Quality)
    @property
    def quality(self) -> Quality:
        high_quality_pattern = r"\b(4k)\b"
        medium_quality_pattern = r"\b(1080p)\b"
        low_quality_pattern = r"\b(720p)\b"
        very_low_quality_pattern = r"\b(480p|360p)\b"

        if re.search(high_quality_pattern, self.title, re.IGNORECASE):
            return Quality.uhd
        elif re.search(medium_quality_pattern, self.title, re.IGNORECASE):
            return Quality.fullhd
        elif re.search(low_quality_pattern, self.title, re.IGNORECASE):
            return Quality.hd
        elif re.search(very_low_quality_pattern, self.title, re.IGNORECASE):
            return Quality.sd

        return Quality.unknown

    @computed_field(return_type=list[int])
    @property
    def season(self) -> list[int]:
        pattern = r"\b[sS](\d+)\b"
        matches = re.findall(pattern, self.title, re.IGNORECASE)
        if matches.__len__() == 2:
            result = []
            for i in range(int(matches[0]), int(matches[1]) + 1):
                result.append(i)
        elif matches.__len__() == 1:
            result = [int(matches[0])]
        else:
            result = []
        return result

    def __gt__(self, other) -> bool:
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

    def __lt__(self, other) -> bool:
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
