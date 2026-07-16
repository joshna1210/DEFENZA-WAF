import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB_NAME", "ai_waf_test")

import pytest


class FakeAsyncCollection:
    """Minimal stand-in for a motor collection. Records every call instead
    of hitting a real MongoDB instance, since these tests only care that
    analysis_service calls the collection with the right documents/filters."""

    def __init__(self):
        self.inserted = []
        self.updated = []

    async def insert_one(self, doc):
        self.inserted.append(doc)
        return type("Result", (), {"inserted_id": doc.get("_id", "fake-id")})()

    async def update_one(self, filter_, update):
        self.updated.append((filter_, update))
        return type("Result", (), {"modified_count": 1})()


@pytest.fixture
def fake_collections(monkeypatch):
    """Patches the collection getters used by analysis_service so
    analyze_and_store() never touches a real database."""
    from app.services import analysis_service

    analysis_results = FakeAsyncCollection()
    traffic_logs = FakeAsyncCollection()

    monkeypatch.setattr(analysis_service, "analysis_results", lambda: analysis_results)
    monkeypatch.setattr(analysis_service, "traffic_logs", lambda: traffic_logs)

    return {"analysis_results": analysis_results, "traffic_logs": traffic_logs}


class _FakeScheduler:
    """app.main.scheduler is a module-level AsyncIOScheduler singleton tied
    to a specific event loop. Each TestClient spins up its own event loop,
    so reusing the real scheduler across tests raises "event loop is
    closed" / ConflictingIdError on the second test. Route tests don't
    exercise the blockchain batch job, so a no-op stub sidesteps all of it."""

    def add_job(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def shutdown(self):
        pass


@pytest.fixture
def client(monkeypatch):
    """FastAPI TestClient with the app's lifespan network calls neutered
    (no real MongoDB/blockchain scheduler dependency needed for route tests)
    and the auth dependency overridden to a fixed admin user."""
    from app.main import app
    from app.middlewares.security_middleware import get_current_user

    async def fake_ensure_indexes():
        return None

    monkeypatch.setattr("app.main.ensure_indexes", fake_ensure_indexes)
    monkeypatch.setattr("app.main.scheduler", _FakeScheduler())

    app.dependency_overrides[get_current_user] = lambda: {"sub": "tester", "role": "admin"}

    from starlette.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
