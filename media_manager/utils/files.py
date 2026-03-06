from pathlib import Path, UnsupportedOperation
import re

from media_manager.config import MediaManagerConfig
from media_manager.torrent.utils import log
import shutil


def import_subtitle(subtitle_file: Path, target_file: str) -> None:
    subtitle_pattern = r"[. ]?([a-z]{2,3})(?:\.(\d+))?\.srt$"
    regex_result = re.search(subtitle_pattern, subtitle_file.name, re.IGNORECASE)
    if regex_result:
        language_code = regex_result.group(1)
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
