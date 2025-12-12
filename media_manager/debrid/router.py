from fastapi import APIRouter, HTTPException, Depends, Request
from media_manager.debrid.schemas import (
    DebridCacheStatus,
    DebridTorrentInfo,
    DebridDirectLink,
    DebridProviderInfo,
    DebridError,
    DebridDownloadRequest
)
from media_manager.debrid.service import debrid_service
import asyncio

router = APIRouter()

# Limit concurrent cache checks to prevent API overload
_cache_check_semaphore = asyncio.Semaphore(2)

@router.get("/provider", response_model=DebridProviderInfo)
async def get_provider_info():
    return debrid_service.get_provider_info()

@router.get("/cache", response_model=DebridCacheStatus)
async def check_cache(hash: str, request: Request):
    # Check if client disconnected before doing expensive work
    if await request.is_disconnected():
        raise HTTPException(status_code=499, detail="Client closed request")
    
    # Acquire slot (max 2 concurrent checks)
    async with _cache_check_semaphore:
        # Check again after waiting for slot
        if await request.is_disconnected():
            raise HTTPException(status_code=499, detail="Client closed request")
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, debrid_service.check_cache, hash)
            return result
        except DebridError as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/torrent", response_model=str)
async def add_torrent(magnet: str):
    try:
        return debrid_service.add_magnet(magnet)
    except DebridError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/torrent/{torrent_id}", response_model=DebridTorrentInfo)
async def get_torrent_info(torrent_id: str):
    try:
        return debrid_service.get_torrent_info(torrent_id)
    except DebridError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/link", response_model=DebridDirectLink)
async def get_download_link(torrent_id: str, file_id: str, filename: str, size: int):
    try:
        return debrid_service.get_download_link(torrent_id, file_id, filename, size)
    except DebridError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/download", response_model=bool)
async def download_file(request: DebridDownloadRequest):
    try:
        return debrid_service.download_file(request.torrent_id, request.file_id, request.destination)
    except DebridError as e:
        raise HTTPException(status_code=400, detail=str(e))
