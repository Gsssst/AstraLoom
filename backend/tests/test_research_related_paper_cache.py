"""Regression tests for cached research related-paper recommendations."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import research


class _CommitSession:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True


def _project(**kwargs):
    defaults = {
        "id": uuid4(),
        "name": "Grounded research agents",
        "description": "Evidence based research workflows",
        "keywords": ["agents", "retrieval"],
        "paper_ids": ["paper-1"],
        "metadata_json": {},
        "user_id": uuid4(),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_related_paper_serialization_uses_external_id_when_local_id_missing():
    paper = SimpleNamespace(
        id=None,
        title="External Paper",
        year=2026,
        arxiv_id="2606.99999",
    )

    items = research._serialize_related_papers([(paper, 0.8, "arxiv:2606.99999")])

    assert items[0]["id"] == "ext:2606.99999"


@pytest.mark.asyncio
async def test_recommended_papers_returns_valid_cache_without_recomputing(monkeypatch):
    project = _project()
    cache_key = research._related_paper_cache_key(project)
    cached_items = [{
        "id": "paper-1",
        "title": "Cached Paper",
        "year": 2026,
        "arxiv_id": "2601.00001",
        "source": "manual",
        "score": 0.99,
    }]
    project.metadata_json = {
        "related_paper_recommendations": {
            "key": cache_key,
            "items": cached_items,
            "refreshed_at": "2026-06-07T00:00:00+00:00",
        }
    }

    async def fake_project(*_args, **_kwargs):
        return project

    def fail_selector(*_args, **_kwargs):
        raise AssertionError("selector should not be constructed for valid cache")

    monkeypatch.setattr(research, "_get_workspace_accessible_project", fake_project)
    monkeypatch.setattr("app.services.paper_selection.PaperSelectionService", fail_selector)

    response = await research.get_recommended_papers(
        project_id=str(project.id),
        refresh=False,
        db=_CommitSession(),
        current_user=SimpleNamespace(id=project.user_id),
    )

    assert response.cached is True
    assert response.refreshed_at == "2026-06-07T00:00:00+00:00"
    assert response.items[0].title == "Cached Paper"


@pytest.mark.asyncio
async def test_recommended_papers_refresh_recomputes_and_updates_cache(monkeypatch):
    project = _project(metadata_json={
        "related_paper_recommendations": {
            "key": "old",
            "items": [],
            "refreshed_at": "2026-06-01T00:00:00+00:00",
        }
    })
    session = _CommitSession()
    selected_paper = SimpleNamespace(
        id=uuid4(),
        title="Fresh Paper",
        year=2026,
        arxiv_id="2606.00001",
    )
    calls = []

    async def fake_project(*_args, **_kwargs):
        return project

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        async def select_papers(self, **kwargs):
            calls.append(kwargs)
            return [(selected_paper, 0.875, "semantic:fresh")]

    monkeypatch.setattr(research, "_get_workspace_accessible_project", fake_project)
    monkeypatch.setattr("app.services.paper_selection.PaperSelectionService", FakeSelector)

    response = await research.get_recommended_papers(
        project_id=str(project.id),
        refresh=True,
        db=session,
        current_user=SimpleNamespace(id=project.user_id),
    )

    cache = project.metadata_json["related_paper_recommendations"]
    assert response.cached is False
    assert response.items[0].title == "Fresh Paper"
    assert response.items[0].score == 0.875
    assert cache["key"] == research._related_paper_cache_key(project)
    assert cache["items"][0]["title"] == "Fresh Paper"
    assert session.committed is True
    assert calls[0]["topic_name"] == project.name
