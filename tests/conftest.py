import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.db import db as db_module
from app.main import app


@pytest.fixture(autouse=True)
def configure_test_env(tmp_path, monkeypatch):
    test_db = tmp_path / "test_jobs.db"
    monkeypatch.setattr(settings, "db_path", str(test_db))
    monkeypatch.setattr(settings, "api_key", "test-api-key")
    monkeypatch.setattr(settings, "worker_poll_interval", 0.01)
    monkeypatch.setenv("API_KEY", "test-api-key")
    db_module._db = None
    yield
    db_module._db = None


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    return {"X-API-Key": settings.api_key}
