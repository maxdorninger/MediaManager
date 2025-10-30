from fastapi.exceptions import HTTPException

from fastapi import APIRouter
from fastapi import status
from fastapi.params import Depends

from media_manager.auth.users import current_active_user, current_superuser
from media_manager.torrent.dependencies import (
    torrent_service_dep,
    torrent_dep,
    torrent_repository_dep,
)
from media_manager.torrent.schemas import Torrent, TorrentStatus

router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_active_user)],
    response_model=list[Torrent],
)
def get_all_torrents(service: torrent_service_dep):
    return service.get_all_torrents()


@router.get("/{torrent_id}", status_code=status.HTTP_200_OK, response_model=Torrent)
def get_torrent(service: torrent_service_dep, torrent: torrent_dep):
    return service.get_torrent_by_id(torrent_id=torrent.id)


@router.delete(
    "/{torrent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def delete_torrent(
    service: torrent_service_dep,
    torrent: torrent_dep,
    delete_files: bool = False,
):
    try:
        service.cancel_download(torrent=torrent, delete_files=delete_files)
    except RuntimeError:
        pass

    service.delete_torrent(torrent_id=torrent.id)


@router.post(
    "/{torrent_id}/retry",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
def retry_torrent_download(
    service: torrent_service_dep,
    torrent: torrent_dep,
):
    service.pause_download(torrent=torrent)
    service.resume_download(torrent=torrent)


@router.patch(
    "/{torrent_id}/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(current_superuser)],
    response_model=Torrent,
)
def update_torrent_status(
    rep: torrent_repository_dep,
    torrent: torrent_dep,
    state: TorrentStatus | None = None,
    imported: bool | None = None,
):
    if imported is not None:
        torrent.imported = imported
    if state is not None:
        torrent.status = state
    if state is None and imported is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No status or imported value provided",
        )

    rep.save_torrent(torrent=torrent)
    return torrent
