"""Tests for database migration health checks."""

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import ProgrammingError

from app.main import app
from app.services import database_health


class _FakeResult:
    def __init__(self, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def fetchall(self):
        return self._rows


class _FakeSession:
    def __init__(self, scalar="alembic_version", rows=None, error=None):
        self.scalar = scalar
        self.rows = rows or []
        self.error = error
        self.rolled_back = False
        self.calls = 0

    async def execute(self, _statement):
        if self.error is not None:
            raise self.error
        self.calls += 1
        if self.calls == 1:
            return _FakeResult(scalar=self.scalar)
        return _FakeResult(rows=self.rows)

    async def rollback(self):
        self.rolled_back = True


@pytest.mark.asyncio
async def test_migration_status_is_ok_when_database_matches_head(monkeypatch):
    monkeypatch.setattr(database_health, "get_code_head_revision", lambda: "025")

    status = await database_health.get_database_migration_status(
        _FakeSession(rows=[("025",)])
    )

    assert status.status == "ok"
    assert status.database == "ok"
    assert status.current_revision == "025"
    assert status.head_revision == "025"
    assert status.is_current is True


@pytest.mark.asyncio
async def test_migration_status_requires_migration_when_revision_lags(monkeypatch):
    monkeypatch.setattr(database_health, "get_code_head_revision", lambda: "025")

    status = await database_health.get_database_migration_status(
        _FakeSession(rows=[("024",)])
    )

    assert status.status == "migration_required"
    assert status.database == "ok"
    assert status.current_revision == "024"
    assert status.head_revision == "025"
    assert status.is_current is False
    assert "alembic upgrade head" in status.detail


@pytest.mark.asyncio
async def test_migration_status_handles_unversioned_database(monkeypatch):
    monkeypatch.setattr(database_health, "get_code_head_revision", lambda: "025")

    status = await database_health.get_database_migration_status(
        _FakeSession(scalar=None)
    )

    assert status.status == "migration_required"
    assert status.current_revision is None
    assert status.head_revision == "025"
    assert status.is_current is False
    assert "not versioned" in status.detail


@pytest.mark.asyncio
async def test_migration_status_reports_database_errors(monkeypatch):
    monkeypatch.setattr(database_health, "get_code_head_revision", lambda: "025")
    session = _FakeSession(
        error=ProgrammingError("SELECT 1", {}, Exception("database unavailable"))
    )

    status = await database_health.get_database_migration_status(session)

    assert status.status == "error"
    assert status.database == "error"
    assert status.head_revision == "025"
    assert session.rolled_back is True


def test_database_health_route_is_registered():
    routes = [
        route
        for route in app.routes
        if route.path == "/api/health/db" and "GET" in (route.methods or set())
    ]

    assert len(routes) == 1
