from fastapi import APIRouter
from fastapi import status
from fastapi.params import Depends

from media_manager.auth.users import current_active_user, current_superuser
from media_manager.torrent.dependencies import torrent_service_dep, torrent_dep
from media_manager.torrent.schemas import Torrent

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
