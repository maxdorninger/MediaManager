from media_manager.indexer.schemas import IndexerQueryResult


class GenericIndexer(object):
    name: str

    def __init__(self, name: str = None):
        if name:
            self.name = name
        else:
            raise ValueError("indexer name must not be None")

    def search(
        self,
        query: str,
        is_tv: bool,
        imdb_id: str | None = None,
        season: int | None = None,
    ) -> list[IndexerQueryResult]:
        """
        Sends a search request to the Indexer and returns the results.

        :param is_tv: Whether to search for TV shows or movies.
        :param query: The search query to send to the Indexer.
        :param imdb_id: The IMDB ID of the movie or show.
        :param season: The season number of the show.
        :param episode: The episode number of the season.
        :return: A list of IndexerQueryResult objects representing the search results.
        """
        raise NotImplementedError()
