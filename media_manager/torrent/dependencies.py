from typing import Annotated

from fastapi import Depends
from fastapi.exceptions import HTTPException

from media_manager.database import DbSessionDependency
from media_manager.exceptions import NotFoundError
from media_manager.torrent.repository import TorrentRepository
from media_manager.torrent.schemas import Torrent, TorrentId
from media_manager.torrent.service import TorrentService


def get_torrent_repository(db: DbSessionDependency) -> TorrentRepository:
    return TorrentRepository(db=db)


torrent_repository_dep = Annotated[TorrentRepository, Depends(get_torrent_repository)]


def get_torrent_service(torrent_repository: torrent_repository_dep) -> TorrentService:
    return TorrentService(torrent_repository=torrent_repository)


torrent_service_dep = Annotated[TorrentService, Depends(get_torrent_service)]


def get_torrent_by_id(
    torrent_service: torrent_service_dep, torrent_id: TorrentId
) -> Torrent:
    """
    Retrieves a torrent by its ID.

    :param torrent_service: The TorrentService instance.
    :param torrent_id: The ID of the torrent to retrieve.
    :return: The TorrentService instance with the specified torrent.
    """
    try:
        torrent = torrent_service.get_torrent_by_id(torrent_id=torrent_id)
    except NotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Torrent with ID {torrent_id} not found"
        ) from None
    return torrent


torrent_dep = Annotated[Torrent, Depends(get_torrent_by_id)]
