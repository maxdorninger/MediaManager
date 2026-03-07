import mimetypes
import re
import shutil
from pathlib import Path, UnsupportedOperation

import patoolib

from media_manager.config import MediaManagerConfig
from media_manager.torrent.schemas import Quality, Torrent
from media_manager.utils import log


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

def extract_quality_video_file(file: Path) -> Quality:
    """
    Extracts the quality of a video file based on its name.

    :param file: The path to the video file.
    :return: The extracted quality or None if not found.
    """
    quality_pattern = r"\b(4k|UHD|ultra[ ._-]?hd|2160p|FHD|full[ ._-]?hd|1080p|HD|720p|SD|480p)\b"
    match = re.search(quality_pattern, file.stem, re.IGNORECASE)
    if match:
        quality = match.group(1).lower()
        if quality in {"4k", "uhd", "2160p"}:
            return Quality.uhd
        if quality in {"fhd", "1080p", "hd"}:
            return Quality.fullhd
        if quality in {"720p"}:
            return Quality.hd
        if quality in {"sd", "480p"}:
            return Quality.sd
    return Quality.unknown


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


def get_importable_media_directories(path: Path) -> list[Path]:
    libraries = [
        *MediaManagerConfig().misc.movie_libraries,
        *MediaManagerConfig().misc.tv_libraries,
    ]

    library_paths = {Path(library.path).absolute() for library in libraries}

    unfiltered_dirs = [d for d in path.glob("*") if d.is_dir()]

    return [
        media_dir
        for media_dir in unfiltered_dirs
        if media_dir.absolute() not in library_paths
        and not media_dir.name.startswith(".")
    ]


def get_torrent_filepath(torrent: Torrent) -> Path:
    return MediaManagerConfig().misc.torrent_directory / torrent.title


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
        else:
            log.debug(f"Unknown file type, will not be imported: {file}")

    log.info(
        f"Found {len(all_files)} files ({len(video_files)} video files, {len(subtitle_files)} subtitle files) for further processing."
    )
    return video_files, subtitle_files, all_files


def import_subtitle(subtitle_file: Path, target_file: str) -> None:
    """
    Imports a subtitle file by renaming it to match the target video file and placing it in the same directory.

    :param subtitle_file: The path to the subtitle file to be imported.
    :return None
    """
    subtitle_pattern = r"[. ]?([a-z]{2,3})(?:\.(\d+))?\.srt$"
    regex_result = re.search(subtitle_pattern, subtitle_file.name, re.IGNORECASE)
    if regex_result:
        language_code = regex_result.group(1)
        if regex_result.group(2):
            language_code += f".{regex_result.group(2)}"
        target_subtitle_file = target_file.with_suffix(f".{language_code}.srt")
        import_file(target_file=target_subtitle_file, source_file=subtitle_file)
    else:
        log.debug(
            f"Didn't find any pattern {subtitle_pattern} in subtitle file: {subtitle_file.name}"
        )


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
