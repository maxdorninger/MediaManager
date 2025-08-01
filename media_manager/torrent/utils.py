import hashlib
import logging
import mimetypes
import re
from pathlib import Path
import shutil

import bencoder
import patoolib
import requests
import libtorrent
from media_manager.config import AllEncompassingConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.torrent.schemas import Torrent

log = logging.getLogger(__name__)


def list_files_recursively(path: Path = Path(".")) -> list[Path]:
    files = list(path.glob("**/*"))
    log.debug(f"Found {len(files)} entries via glob")
    valid_files = []
    for x in files:
        if x.is_dir():
            log.debug(f"'{x}' is a directory")
        elif x.is_symlink():
            log.debug(f"'{x}' is a symlink")
        else:
            valid_files.append(x)
    log.debug(f"Returning {len(valid_files)} files after filtering")
    return valid_files


def extract_archives(files):
    archive_types = {
        "application/zip",
        "application/x-zip-compressedapplication/x-compressed",
        "application/vnd.rar",
        "application/x-7z-compressed",
        "application/x-freearc",
        "application/x-bzip",
        "application/x-bzip2",
        "application/gzip",
        "application/x-gzip",
        "application/x-tar",
    }
    for file in files:
        file_type = mimetypes.guess_type(file)
        log.debug(f"File: {file}, Size: {file.stat().st_size} bytes, Type: {file_type}")

        if file_type[0] in archive_types:
            log.info(
                f"File {file} is a compressed file, extracting it into directory {file.parent}"
            )
            try:
                patoolib.extract_archive(str(file), outdir=str(file.parent))
            except patoolib.util.PatoolError as e:
                log.error(f"Failed to extract archive {file}. Error: {e}")


def get_torrent_filepath(torrent: Torrent):
    return AllEncompassingConfig().misc.torrent_directory / torrent.title


def import_file(target_file: Path, source_file: Path):
    if target_file.exists():
        target_file.unlink()
    try:
        target_file.hardlink_to(source_file)
    except FileExistsError:
        log.error(f"File already exists at {target_file}. ")
    except OSError as e:
        log.error(
            f"Failed to create hardlink from {source_file} to {target_file}: {e}. "
            "Falling back to copying the file."
        )
        shutil.copy(src=source_file, dst=target_file)


def import_torrent(torrent: Torrent) -> (list[Path], list[Path], list[Path]):
    """
    Extracts all files from the torrent download directory, including extracting archives.
    Returns a tuple containing: seperated video files, subtitle files, and all files found in the torrent directory.
    """
    log.info(f"Importing torrent {torrent}")
    all_files = list_files_recursively(path=get_torrent_filepath(torrent=torrent))
    log.debug(f"Found {len(all_files)} files downloaded by the torrent")
    extract_archives(all_files)
    all_files = list_files_recursively(path=get_torrent_filepath(torrent=torrent))

    video_files = []
    subtitle_files = []
    for file in all_files:
        file_type, _ = mimetypes.guess_type(str(file))
        if file_type is not None:
            if file_type.startswith("video"):
                video_files.append(file)
                log.debug(f"File is a video, it will be imported: {file}")
            elif file_type.startswith("text") and Path(file).suffix == ".srt":
                subtitle_files.append(file)
                log.debug(f"File is a subtitle, it will be imported: {file}")
            else:
                log.debug(
                    f"File is neither a video nor a subtitle, will not be imported: {file}"
                )

    log.info(
        f"Found {len(all_files)} files ({len(video_files)} video files, {len(subtitle_files)} subtitle files) for further processing."
    )
    return video_files, subtitle_files, all_files


def get_torrent_hash(torrent: IndexerQueryResult) -> str:
    """
    Helper method to get the torrent hash from the torrent object.

    :param torrent: The torrent object.
    :return: The hash of the torrent.
    """
    torrent_filepath = (
        AllEncompassingConfig().misc.torrent_directory / f"{torrent.title}.torrent"
    )
    if torrent_filepath.exists():
        log.warning(f"Torrent file already exists at: {torrent_filepath}")

    if torrent.download_url.startswith("magnet:"):
        log.info(f"Parsing torrent with magnet URL: {torrent.title}")
        log.debug(f"Magnet URL: {torrent.download_url}")
        torrent_hash = str(libtorrent.parse_magnet_uri(torrent.download_url).info_hash)
    else:
        # downloading the torrent file
        log.info(f"Downloading .torrent file of torrent: {torrent.title}")
        try:
            response = requests.get(str(torrent.download_url), timeout=30)
            response.raise_for_status()
            torrent_content = response.content
        except Exception as e:
            log.error(f"Failed to download torrent file: {e}")
            raise

        # saving the torrent file
        with open(torrent_filepath, "wb") as file:
            file.write(torrent_content)

        # parsing info hash
        log.debug(f"parsing torrent file: {torrent.download_url}")
        try:
            decoded_content = bencoder.decode(torrent_content)
            torrent_hash = hashlib.sha1(
                bencoder.encode(decoded_content[b"info"])
            ).hexdigest()
        except Exception as e:
            log.error(f"Failed to decode torrent file: {e}")
            raise
    return torrent_hash


def remove_special_characters(filename: str) -> str:
    """
    Removes special characters from the filename to ensure it works with Jellyfin.

    :param filename: The original filename.
    :return: A sanitized version of the filename.
    """
    # Remove invalid characters
    sanitized = re.sub(r"([<>:\"/\\|?*])", "", filename)

    # Remove leading and trailing dots or spaces
    sanitized = sanitized.strip(" .")

    return sanitized
