"""Debrid API Router - HTTP endpoints for debrid operations."""
import asyncio

from fastapi import APIRouter, HTTPException, Request

from media_manager.debrid.schemas import (
    DebridCacheStatus,
    DebridDirectLink,
    DebridDownloadRequest,
    DebridError,
    DebridProviderInfo,
    DebridTorrentInfo,
)
from media_manager.debrid.service import debrid_service

router = APIRouter()

# Limit concurrent cache checks to prevent API rate limit issues
_cache_semaphore = asyncio.Semaphore(2)


@router.get("/provider", response_model=DebridProviderInfo)
async def get_provider_info():
    """Get info about the active debrid provider."""
    return debrid_service.get_provider_info()


@router.get("/cache", response_model=DebridCacheStatus)
async def check_cache(hash: str, request: Request):
    """Check if torrent is cached on any configured debrid provider."""
    if await request.is_disconnected():
        raise HTTPException(status_code=499, detail="Client disconnected")

    async with _cache_semaphore:
        if await request.is_disconnected():
            raise HTTPException(status_code=499, detail="Client disconnected")

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, debrid_service.check_cache, hash)
        except DebridError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/torrent", response_model=str)
async def add_torrent(magnet: str):
    """Add magnet link to debrid service."""
    try:
        return debrid_service.add_magnet(magnet)
    except DebridError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/torrent/{torrent_id}", response_model=DebridTorrentInfo)
async def get_torrent_info(torrent_id: str):
    """Get torrent details including file list."""
    try:
        result = debrid_service.get_torrent_info(torrent_id)
        if not result:
            raise HTTPException(status_code=404, detail="Torrent not found")
        return result
    except DebridError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/link", response_model=DebridDirectLink)
async def get_download_link(torrent_id: str, file_id: str, filename: str = "", size: int = 0):
    """Get direct download link for a file."""
    try:
        return debrid_service.get_download_link(torrent_id, file_id, filename, size)
    except DebridError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download", response_model=str)
async def download_file(request: DebridDownloadRequest):
    """Download file from debrid to local filesystem."""
    try:
        return debrid_service.download_file(
            request.torrent_id,
            request.file_id,
            request.destination,
        )
    except DebridError as e:
        raise HTTPException(status_code=400, detail=str(e))
