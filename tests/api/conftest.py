import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    # Import inside the fixture so CONFIG_FILE / DISABLE_FRONTEND_MOUNT (set
    # by the root conftest) are in place before main.py runs at import time.
    from media_manager.main import app

    return TestClient(app)
