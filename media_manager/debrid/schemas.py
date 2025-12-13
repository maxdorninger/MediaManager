from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class DebridProvider(str, Enum):
    TorBox = "torbox"
    RealDebrid = "realdebrid"
    AllDebrid = "alldebrid"

class DebridProviderInfo(BaseModel):
    id: DebridProvider
    name: str
    description: str
    website: str
    color: str
    is_implemented: bool
    supports_cache_check: bool
    rate_limit_seconds: float = 0.0

class DebridCacheStatus(BaseModel):
    is_cached: bool
    provider: Optional[DebridProvider] = None  # Which provider has the cache
    name: Optional[str] = None
    size: Optional[int] = None
    hash: str

class DebridFile(BaseModel):
    id: str
    name: str
    short_name: str
    size: int

class DebridTorrentInfo(BaseModel):
    id: str
    name: str
    size: int
    hash: str
    files: List[DebridFile]

class DebridTorrentStatus(BaseModel):
    id: str
    status: str
    is_ready: bool
    progress: float
    speed: Optional[int]
    seeders: Optional[int]
    name: str
    size: int

class DebridDirectLink(BaseModel):
    url: str
    filename: str
    size: int

class DebridDownloadRequest(BaseModel):
    torrent_id: str
    file_id: str
    destination: str

class DebridError(Exception):
    def __init__(self, message: str, code: str = "api_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)
