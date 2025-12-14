import typing
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, BaseModel, Field

from media_manager.torrent.schemas import Quality, Torrent

if TYPE_CHECKING:
    from datetime import timedelta

NzbId = typing.NewType("NzbId", uuid.UUID)


class NzbStatus(Enum):
    """
    Defines MediaManager's simplified Nzb statuses.
    """
    finished = 1
    # File(s) are finished downloading and processing, and are ready to move.
    downloading = 2
    # File(s) are downloading.
    error = 3
    # File(s) failed to download.
    unknown = 4
    # Unable to obtain status of download.
    processing = 5
    # File(s) are downloaded and processing before completion.


class Nzb(Torrent):
    model_config = ConfigDict(from_attributes=True)

    id: NzbId = Field(default_factory=uuid.uuid4)
    status: NzbStatus
    title: str
    quality: Quality
    imported: bool
    hash: str
    usenet: bool = True


class SabnzbdStatus(Enum):
    """
    Defines all Sabnzbd nzb statuses.
    """
    ###########################
    # in progress nzb download statuses.
    ##########################
    Downloading = "Downloading"
    # Downloading the file
    Paused = "Paused"
    # Individual download and/or entire download queue is paused
    Propagating = "Propagating"
    # Download is delayed
    ###########################
    # downloaded nzb statuses.
    ##########################
    Completed = "Completed"
    # Download and processing is complete
    Failed = "Failed"
    # Download failed
    QuickCheck = "QuickCheck"
    # Fast integrity check of download
    Verifying = "Verifying"
    # Running SFV-based integrity check
    Repairing = "Repairing"
    # Attempting to repair the incomplete download
    Extracting = "Extracting"
    # Extracting the completed download archives
    Moving = "Moving"
    # Moving the final media file to its destination
    Running = "Running"
    # Post-processing script is running
    ###########################
    # statuses for both in progress and downloaded nzbs.
    ##########################
    Fetching = "Fetching"
    # Job is downloading extra par2 files
    Queued = "Queued"
    # Download is queued, or if finished, waiting for post-processing
    Unknown = "Unknown"
    # Download status was not found.


class SabnzbdDownloadDetailsBase(BaseModel):
    nzo_id: str
    name: str #filename, # Name given to the download by requester
    time_added: int
    status: Enum
    category: str
    size_total: str #size
    password: str
    script: str #enum??

class SabnzbdDownloadDetailsInProgress(SabnzbdDownloadDetailsBase):
    index: int
    unpackopts: int
    priority: str #enum?
    labels: []
    mbleft: float
    mbtotal: float #"mb"
    sizeleft: str
    percentage: int
    mbmissing: float
    direct_unpack: str
    timeleft: timedelta
    avg_age: str

class SabnzbdDownloadDetailsCompleted(SabnzbdDownloadDetailsBase):
    completed: int
    nzb_name: str # File name of the NZB
    pp: str#??
    report: str
    url: str
    storage: str
    path: str
    script_line: str
    download_time: int #duration
    postproc_time: int #duration
    stage_log: []
    downloaded: int #epoch
    completeness: str
    fail_message: str
    url_info: str
    bytes: int
    meta: str
    series: str
    md5sum: str
    duplicate_key: str
    archive: bool # aka needs to be extracted
    action_line: str
    loaded: bool
    retry: bool

def sabnzbd_to_nzb_status(status: str or SabnzbdStatus) -> NzbStatus:
    """
    Reduces any Sabnzbd status into a simplified Nzb status.
    """
    if isinstance(status, str):
        status = SabnzbdStatus(status)

    if status in [
        SabnzbdStatus.Fetching,
        SabnzbdStatus.Queued,
        SabnzbdStatus.Paused,
        SabnzbdStatus.Propagating,
    ]:
        return NzbStatus.downloading
    elif status in [
        SabnzbdStatus.QuickCheck,
        SabnzbdStatus.Verifying,
        SabnzbdStatus.Extracting,
        SabnzbdStatus.Moving,
        SabnzbdStatus.Running,
    ]:
        return NzbStatus.processing
    elif status is SabnzbdStatus.Completed:
        return NzbStatus.finished
    elif status is SabnzbdStatus.Failed:
        return NzbStatus.error
    else:
        return NzbStatus.unknown
