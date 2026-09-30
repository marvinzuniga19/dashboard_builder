from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import BACKEND_DIR, Settings, get_settings
from app.core.database import build_engine
from app.main import app


def test_health_checks_database() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_cors_allows_only_configured_origin() -> None:
    with TestClient(app) as client:
        accepted = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
        assert accepted.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert accepted.headers["access-control-allow-credentials"] == "true"
        rejected = client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
        assert "access-control-allow-origin" not in rejected.headers


def test_errors_have_consistent_shape() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/missing")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "HTTP_404"


def test_database_path_is_anchored_to_backend() -> None:
    settings = Settings(_env_file=None, database_url="sqlite+aiosqlite:///./data/test.db")
    assert Path(str(settings.database_connection_url.database)) == BACKEND_DIR / "data/test.db"


def test_tests_never_touch_the_development_database() -> None:
    """Si un import de la app ocurre antes de fijar DATABASE_URL, todo el
    esquema de pruebas acabaría aplicado sobre backend/data/dashboard.db."""
    database_path = Path(str(get_settings().database_connection_url.database))
    assert "dashboard-builder-tests-" in str(database_path)
    assert database_path != BACKEND_DIR / "data/dashboard.db"


@pytest.mark.asyncio
async def test_sqlite_pragmas_on_each_connection() -> None:
    engine = build_engine()
    try:
        async with engine.connect() as first, engine.connect() as second:
            for connection in (first, second):
                assert (await connection.execute(text("PRAGMA foreign_keys"))).scalar() == 1
                assert (await connection.execute(text("PRAGMA journal_mode"))).scalar() == "wal"
    finally:
        await engine.dispose()
