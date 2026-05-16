"""Bare Minimum smoke tests for FastAPI app: the app boots,
the health endpoint responds, OpenAPI is generated,
and protected endpoints reject anonymous requests.
"""

from fastapi import status
from fastapi.testclient import TestClient


class TestHealth:
    def test_health_endpoint_returns_message(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "Hello World" in body["message"]
        # version comes from PUBLIC_VERSION; unset in tests → None
        assert "version" in body


class TestOpenAPI:
    def test_openapi_schema_is_served(self, client: TestClient) -> None:
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK
        schema = response.json()
        assert schema["openapi"].startswith("3.")
        assert "/api/v1/health" in schema["paths"]

    def test_known_routers_are_mounted(self, client: TestClient) -> None:
        # Surface-level guard against an accidentally-removed include_router
        # call in main.py. Doesn't validate individual endpoint shapes.
        paths = client.get("/openapi.json").json()["paths"]
        assert any(p.startswith("/api/v1/tv/") for p in paths)
        assert any(p.startswith("/api/v1/movies/") for p in paths)
        assert any(p.startswith("/api/v1/torrent") for p in paths)
        assert any(p.startswith("/api/v1/notification") for p in paths)


class TestAuthGate:
    def test_protected_endpoint_rejects_anonymous(self, client: TestClient) -> None:
        # /api/v1/tv/shows requires current_active_user. Anonymous request
        # should be rejected; fastapi-users returns 401.
        response = client.get("/api/v1/tv/shows")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
