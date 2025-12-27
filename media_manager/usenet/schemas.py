import typing
import uuid
from enum import Enum

from pydantic import ConfigDict, BaseModel, Field

from media_manager.torrent.schemas import Quality

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


class Nzb(BaseModel):
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

    https://sabnzbd.org/wiki/extra/queue-history-searching
    """
    ###########################
    # in progress nzb download statuses.
    ##########################
    Grabbing = "Grabbing"
    # Getting an NZB from an external site
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
    # Running SFV-based integrity check (by par2)
    Repairing = "Repairing"
    # Job is being repaired (by par2)
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


def sabnzbd_to_nzb_status(status: str or SabnzbdStatus) -> NzbStatus:
    """
    Reduces any Sabnzbd status into a simplified Nzb status.
    """
    if isinstance(status, str):
        status = SabnzbdStatus(status)

    if status in [
        SabnzbdStatus.Downloading,
        SabnzbdStatus.Fetching,
        SabnzbdStatus.Queued,
        SabnzbdStatus.Paused,
        SabnzbdStatus.Propagating,
        SabnzbdStatus.Grabbing,
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
