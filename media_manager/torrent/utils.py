import hashlib
import logging
import mimetypes
import re
import shutil
from pathlib import Path, UnsupportedOperation

import bencoder
import libtorrent
import patoolib
import requests
from pathvalidate import sanitize_filename
from requests.exceptions import InvalidSchema

from media_manager.config import MediaManagerConfig
from media_manager.indexer.schemas import IndexerQueryResult
from media_manager.indexer.utils import follow_redirects_to_final_torrent_url
from media_manager.torrent.schemas import Torrent

log = logging.getLogger(__name__)


def list_files_recursively(path: Path = Path()) -> list[Path]:
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


def extract_archives(files: list) -> None:
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
            except patoolib.util.PatoolError:
                log.exception(f"Failed to extract archive {file}")


def get_torrent_filepath(torrent: Torrent) -> Path:
    return MediaManagerConfig().misc.torrent_directory / torrent.title


def import_file(target_file: Path, source_file: Path) -> None:
    if target_file.exists():
        target_file.unlink()

    try:
        target_file.hardlink_to(source_file)
    except FileExistsError:
        log.exception(f"File already exists at {target_file}.")
    except (OSError, UnsupportedOperation, NotImplementedError):
        log.exception(
            f"Failed to create hardlink from {source_file} to {target_file}. Falling back to copying the file."
        )
        shutil.copy(src=source_file, dst=target_file)


def get_files_for_import(
    torrent: Torrent | None = None, directory: Path | None = None
) -> tuple[list[Path], list[Path], list[Path]]:
    """
    Extracts all files from the torrent download directory, including extracting archives.
    Returns a tuple containing: seperated video files, subtitle files, and all files found in the torrent directory.
    """
    if torrent:
        log.info(f"Importing torrent {torrent}")
        search_directory = get_torrent_filepath(torrent=torrent)
    elif directory:
        log.info(f"Importing files from directory {directory}")
        search_directory = directory
    else:
        msg = "Either torrent or directory must be provided."
        raise ValueError(msg)

    all_files: list[Path] = list_files_recursively(path=search_directory)
    log.debug(f"Found {len(all_files)} files downloaded by the torrent")
    extract_archives(all_files)
    all_files = list_files_recursively(path=search_directory)

    video_files: list[Path] = []
    subtitle_files: list[Path] = []
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


AUDIO_EXTENSIONS = {".flac", ".mp3", ".ogg", ".m4a", ".opus", ".wav", ".aac", ".wma", ".alac"}

BOOK_EXTENSIONS = {".epub", ".mobi", ".pdf", ".azw3", ".fb2", ".cbz", ".cbr", ".m4b"}


def get_audio_files_for_import(
    torrent: Torrent | None = None, directory: Path | None = None
) -> tuple[list[Path], list[Path]]:
    """
    Extracts all files from the torrent download directory, including extracting archives.
    Returns a tuple containing: audio files and all files found in the directory.
    """
    if torrent:
        log.info(f"Importing audio torrent {torrent}")
        search_directory = get_torrent_filepath(torrent=torrent)
    elif directory:
        log.info(f"Importing audio files from directory {directory}")
        search_directory = directory
    else:
        msg = "Either torrent or directory must be provided."
        raise ValueError(msg)

    all_files: list[Path] = list_files_recursively(path=search_directory)
    log.debug(f"Found {len(all_files)} files downloaded by the torrent")
    extract_archives(all_files)
    all_files = list_files_recursively(path=search_directory)

    audio_files: list[Path] = []
    for file in all_files:
        if file.suffix.lower() in AUDIO_EXTENSIONS:
            audio_files.append(file)
            log.debug(f"File is audio, it will be imported: {file}")
        else:
            log.debug(f"File is not audio, will not be imported: {file}")

    log.info(
        f"Found {len(all_files)} files ({len(audio_files)} audio files) for further processing."
    )
    return audio_files, all_files


def get_book_files_for_import(
    torrent: Torrent | None = None, directory: Path | None = None
) -> tuple[list[Path], list[Path]]:
    """
    Extracts all files from the torrent download directory, including extracting archives.
    Returns a tuple containing: book files and all files found in the directory.
    """
    if torrent:
        log.info(f"Importing book torrent {torrent}")
        search_directory = get_torrent_filepath(torrent=torrent)
    elif directory:
        log.info(f"Importing book files from directory {directory}")
        search_directory = directory
    else:
        msg = "Either torrent or directory must be provided."
        raise ValueError(msg)

    all_files: list[Path] = list_files_recursively(path=search_directory)
    log.debug(f"Found {len(all_files)} files downloaded by the torrent")
    extract_archives(all_files)
    all_files = list_files_recursively(path=search_directory)

    book_files: list[Path] = []
    for file in all_files:
        if file.suffix.lower() in BOOK_EXTENSIONS:
            book_files.append(file)
            log.debug(f"File is a book, it will be imported: {file}")
        else:
            log.debug(f"File is not a book, will not be imported: {file}")

    log.info(
        f"Found {len(all_files)} files ({len(book_files)} book files) for further processing."
    )
    return book_files, all_files


def get_torrent_hash(torrent: IndexerQueryResult) -> str:
    """
    Helper method to get the torrent hash from the torrent object.

    :param torrent: The torrent object.
    :return: The hash of the torrent.
    """
    torrent_filepath = (
        MediaManagerConfig().misc.torrent_directory
        / f"{sanitize_filename(torrent.title)}.torrent"
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
        except InvalidSchema:
            log.debug(f"Invalid schema for URL {torrent.download_url}", exc_info=True)
            final_url = follow_redirects_to_final_torrent_url(
                initial_url=torrent.download_url,
                session=requests.Session(),
                timeout=MediaManagerConfig().indexers.prowlarr.timeout_seconds,
            )
            return str(libtorrent.parse_magnet_uri(final_url).info_hash)
        except Exception:
            log.exception("Failed to download torrent file")
            raise

        # saving the torrent file
        torrent_filepath.write_bytes(torrent_content)

        # parsing info hash
        log.debug(f"parsing torrent file: {torrent.download_url}")
        try:
            decoded_content = bencoder.decode(torrent_content)
            torrent_hash = hashlib.sha1(  # noqa: S324
                bencoder.encode(decoded_content[b"info"])
            ).hexdigest()
        except Exception:
            log.exception("Failed to decode torrent file")
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
    return sanitized.strip(" .")


def remove_special_chars_and_parentheses(title: str) -> str:
    """
    Removes special characters and bracketed information from the title.

    :param title: The original title.
    :return: A sanitized version of the title.
    """

    # Remove content within brackets
    sanitized = re.sub(r"\[.*?\]", "", title)

    # Remove content within curly brackets
    sanitized = re.sub(r"\{.*?\}", "", sanitized)

    # Remove year within parentheses
    sanitized = re.sub(r"\(\d{4}\)", "", sanitized)

    # Remove special characters
    sanitized = remove_special_characters(sanitized)

    # Collapse multiple whitespace characters and trim the result
    return re.sub(r"\s+", " ", sanitized).strip()


def get_importable_media_directories(path: Path) -> list[Path]:
    libraries = [
        *MediaManagerConfig().misc.movie_libraries,
        *MediaManagerConfig().misc.tv_libraries,
        *MediaManagerConfig().misc.music_libraries,
        *MediaManagerConfig().misc.books_libraries,
    ]

    library_paths = {Path(library.path).absolute() for library in libraries}

    unfiltered_dirs = [d for d in path.glob("*") if d.is_dir()]

    return [
        media_dir
        for media_dir in unfiltered_dirs
        if media_dir.absolute() not in library_paths
        and not media_dir.name.startswith(".")
    ]


def extract_external_id_from_string(input_string: str) -> tuple[str | None, int | None]:
    """
    Extracts an external ID (tmdb/tvdb ID) from the given string.

    :param input_string: The string to extract the ID from.
    :return: The extracted Metadata Provider and ID or None if not found.
    """
    match = re.search(
        r"\b(tmdb|tvdb)(?:id)?[-_]?([0-9]+)\b", input_string, re.IGNORECASE
    )
    if match:
        return match.group(1).lower(), int(match.group(2))

    return None, None
