import re

from pydantic import BaseModel, computed_field

from database.torrents import QualityMixin, Torrent


class IndexerQueryResult(BaseModel, QualityMixin):
    title: str
    download_url: str
    seeders: int
    flags: list[str]

    def __gt__(self, other) -> bool:
        if self.quality.value != other.quality.value:
            return self.quality.value > other.quality.value
        return self.seeders < other.seeders

    def __lt__(self, other) -> bool:
        if self.quality.value != other.quality.value:
            return self.quality.value < other.quality.value
        return self.seeders > other.seeders

    def download(self) -> Torrent:
        """
        downloads a torrent file and returns the filepath
        """
        import requests
        url = self.download_url
        torrent_filepath = self.title + ".torrent"
        with open(torrent_filepath, 'wb') as out_file:
            content = requests.get(url).content
            out_file.write(content)

        return Torrent(torrent_title=self.title)


    @computed_field
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


class GenericIndexer(object):
    name: str

    def __init__(self, name: str = None):
        if name:
            self.name = name
        else:
            raise ValueError('indexer name must not be None')

    def get_search_results(self, query: str) -> list[IndexerQueryResult]:
        """
        Sends a search request to the Indexer and returns the results.

        :param query: The search query to send to the Indexer.
        :return: A list of IndexerQueryResult objects representing the search results.
        """
        raise NotImplementedError()
