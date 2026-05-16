"""Top-level pytest configuration.

The CONFIG_FILE env var must be set before media_manager.config is imported,
because that module reads it at import time and constructs a settings
instance whose TomlConfigSettingsSource fails if the path does not exist.
We point it at the in-repo example config so unit tests can import freely.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

os.environ.setdefault("CONFIG_FILE", str(REPO_ROOT / "config.example.toml"))
# main.py mounts a StaticFiles route from FRONTEND_FILES_DIR at import time
# unless this flag is set, which would fail in CI where no build exists.
os.environ.setdefault("DISABLE_FRONTEND_MOUNT", "true")
# logging.py defaults LOG_FILE to /app/config/media_manager.log, which the
# RotatingFileHandler tries to open at app startup; redirect to a writable
# temp path so the dict-config doesn't fail when the app is booted in tests.
_TEST_DATA_ROOT = REPO_ROOT / ".pytest_cache" / "data"
_TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "LOG_FILE", str(REPO_ROOT / ".pytest_cache" / "media_manager.log")
)
# config.example.toml points the media directories at /data/* (container
# paths). Override with writable temp paths so run_filesystem_checks
# succeeds when the app is booted in tests. Uses pydantic-settings env
# delimiter `__`.
for _name in ("tv", "movie", "torrent", "image"):
    os.environ.setdefault(
        f"MEDIAMANAGER_MISC__{_name.upper()}_DIRECTORY",
        str(_TEST_DATA_ROOT / _name),
    )

import pytest  # noqa: E402

from media_manager.indexer.config import (  # noqa: E402
    IndexerFlagScoringRule,
    TitleScoringRule,
)
from tests.types import PatchScoringRules  # noqa: E402


@pytest.fixture
def patch_scoring_rules(monkeypatch: pytest.MonkeyPatch) -> PatchScoringRules:
    """Inject scoring rules into the config for the indexer utils module.

    MediaManagerConfig() returns a freshly-loaded instance per call, so we
    can't mutate one instance and expect the next call to see it. Instead,
    replace the symbol that indexer.utils imported so every call inside the
    function under test returns the same pre-built instance.
    """
    import media_manager.indexer.utils as indexer_utils
    from media_manager.config import MediaManagerConfig

    def _apply(
        title: list[TitleScoringRule] | None = None,
        flags: list[IndexerFlagScoringRule] | None = None,
    ) -> None:
        cfg = MediaManagerConfig()
        cfg.indexers.title_scoring_rules = title or []
        cfg.indexers.indexer_flag_scoring_rules = flags or []
        monkeypatch.setattr(indexer_utils, "MediaManagerConfig", lambda: cfg)

    return _apply
