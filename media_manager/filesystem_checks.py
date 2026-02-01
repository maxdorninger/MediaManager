import shutil
from logging import Logger
from pathlib import Path

from media_manager.config import MediaManagerConfig


def run_filesystem_checks(config: MediaManagerConfig, log: Logger) -> None:
    log.info("Creating directories if they don't exist...")
    config.misc.tv_directory.mkdir(parents=True, exist_ok=True)
    config.misc.movie_directory.mkdir(parents=True, exist_ok=True)
    config.misc.torrent_directory.mkdir(parents=True, exist_ok=True)
    config.misc.image_directory.mkdir(parents=True, exist_ok=True)
    log.info("Conducting filesystem tests...")
    test_dir = config.misc.tv_directory / Path(".media_manager_test_dir")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_dir.rmdir()
    log.info(f"Successfully created test dir in TV directory at: {test_dir}")
    test_dir = config.misc.movie_directory / Path(".media_manager_test_dir")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_dir.rmdir()
    log.info(f"Successfully created test dir in Movie directory at: {test_dir}")
    test_dir = config.misc.image_directory / Path(".media_manager_test_dir")
    test_dir.touch()
    test_dir.unlink()
    log.info(f"Successfully created test file in Image directory at: {test_dir}")
    test_dir = config.misc.tv_directory / Path(".media_manager_test_dir")
    test_dir.mkdir(parents=True, exist_ok=True)
    torrent_dir = config.misc.torrent_directory / Path(".media_manager_test_dir")
    torrent_dir.mkdir(parents=True, exist_ok=True)
    test_torrent_file = torrent_dir / Path(".media_manager.test.torrent")
    test_torrent_file.touch()
    test_hardlink = test_dir / Path(".media_manager.test.hardlink")
    try:
        test_hardlink.hardlink_to(test_torrent_file)
        if not test_hardlink.samefile(test_torrent_file):
            log.critical("Hardlink creation failed!")
        log.info("Successfully created test hardlink in TV directory")
    except OSError:
        log.exception("Hardlink creation failed, falling back to copying files")
        shutil.copy(src=test_torrent_file, dst=test_hardlink)
    finally:
        test_hardlink.unlink()
        test_torrent_file.unlink()
        torrent_dir.rmdir()
        test_dir.rmdir()
