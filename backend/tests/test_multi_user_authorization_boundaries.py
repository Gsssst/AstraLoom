"""Regression tests for multi-user authorization boundaries."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import folders, research, usage
from app.core.security import get_current_user, require_admin
from app.main import app
from app.services.usage_tracker import UsageTracker


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _RecordingSession:
    def __init__(self, value=None):
        self.value = value
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _ScalarResult(self.value)


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


@pytest.mark.asyncio
async def test_require_admin_rejects_standard_users():
    with pytest.raises(HTTPException) as error:
        await require_admin(SimpleNamespace(role="user"))

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_require_admin_accepts_administrators():
    admin = SimpleNamespace(role="admin")

    assert await require_admin(admin) is admin


@pytest.mark.asyncio
async def test_owned_project_lookup_filters_by_current_user():
    session = _RecordingSession()
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(HTTPException) as error:
        await research._get_owned_project(session, str(uuid4()), user)

    sql = str(session.statements[0])
    assert "research_projects.id" in sql
    assert "research_projects.user_id" in sql
    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_standard_user_history_is_forced_to_current_user(monkeypatch):
    captured = []

    async def fake_history(user_id=None, limit=50):
        captured.append((user_id, limit))
        return []

    monkeypatch.setattr(UsageTracker, "get_recent_history", fake_history)
    user = SimpleNamespace(id=uuid4(), role="user")

    await usage.get_history(user_id=str(uuid4()), limit=12, user=user)

    assert captured == [(str(user.id), 12)]


@pytest.mark.asyncio
async def test_admin_history_keeps_requested_user_filter(monkeypatch):
    captured = []

    async def fake_history(user_id=None, limit=50):
        captured.append((user_id, limit))
        return []

    monkeypatch.setattr(UsageTracker, "get_recent_history", fake_history)
    requested_user_id = str(uuid4())

    await usage.get_history(
        user_id=requested_user_id,
        limit=8,
        user=SimpleNamespace(id=uuid4(), role="admin"),
    )

    assert captured == [(requested_user_id, 8)]


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/papers/ingest", "POST"),
        ("/api/papers/generate-embeddings", "POST"),
        ("/api/papers/auto-tag-all", "POST"),
        ("/api/papers/{paper_id}/global", "DELETE"),
        ("/api/tasks/download-paper", "POST"),
        ("/api/tasks/{task_id}", "GET"),
        ("/api/usage/all-stats", "GET"),
        ("/api/dashboard/stats", "GET"),
    ],
)
def test_system_wide_routes_require_admin(path, method):
    assert require_admin in _dependency_calls(path, method)


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/research/projects", "GET"),
        ("/api/research/projects/{project_id}", "GET"),
        ("/api/research/projects/{project_id}/generate-ideas", "POST"),
        ("/api/research/projects/{project_id}/idea-runs", "POST"),
        ("/api/research/projects/{project_id}/idea-runs/stream", "POST"),
        ("/api/research/projects/{project_id}/idea-runs/latest", "GET"),
        ("/api/research/idea-runs/{run_id}", "GET"),
        ("/api/research/ideas/compare", "POST"),
        ("/api/research/ideas/{idea_id}", "GET"),
        ("/api/research/ideas/{idea_id}/decision", "PATCH"),
        ("/api/research/ideas/{idea_id}/evolve", "POST"),
        ("/api/research/ideas/{idea_id}/evolve-from-feedback", "POST"),
        ("/api/research/ideas/{idea_id}/lineage", "GET"),
        ("/api/research/projects/{project_id}/evidence/import", "POST"),
        ("/api/folders/", "GET"),
        ("/api/folders/", "POST"),
        ("/api/folders/{folder_id}/papers", "GET"),
        ("/api/folders/{folder_id}/papers", "POST"),
        ("/api/folders/{folder_id}/diagnostics", "GET"),
        ("/api/folders/{folder_id}/paper-ids", "GET"),
        ("/api/folders/{folder_id}/papers/{paper_id}", "DELETE"),
        ("/api/folders/{folder_id}", "DELETE"),
        ("/api/papers/ingest-personal", "POST"),
    ],
)
def test_private_workspace_routes_require_authentication(path, method):
    assert get_current_user in _dependency_calls(path, method)


def test_shared_project_view_remains_public():
    dependencies = _dependency_calls("/api/research/share/{token}", "GET")

    assert get_current_user not in dependencies
    assert require_admin not in dependencies


def test_compare_route_precedes_dynamic_idea_detail_route():
    paths = [route.path for route in app.routes]

    assert paths.index("/api/research/ideas/compare") < paths.index("/api/research/ideas/{idea_id}")


def test_folder_tree_excludes_foreign_children():
    owner_id = uuid4()
    root_id = uuid4()
    owned_child = SimpleNamespace(id=uuid4(), name="owned", parent_id=root_id, user_id=owner_id, children=[])
    foreign_child = SimpleNamespace(id=uuid4(), name="foreign", parent_id=root_id, user_id=uuid4(), children=[])
    root = SimpleNamespace(id=root_id, name="root", parent_id=None, user_id=owner_id, children=[owned_child, foreign_child])

    tree = folders.build_tree(root, owner_id, {str(root_id): 3})

    assert [child["name"] for child in tree["children"]] == ["owned"]
    assert tree["paper_count"] == 3


def test_research_project_create_accepts_collection_seed_papers():
    paper_id = str(uuid4())
    collection_id = str(uuid4())
    req = research.ProjectCreate(name="Video grounding", paper_ids=[paper_id], collection_ids=[collection_id])

    assert req.paper_ids == [paper_id]
    assert req.collection_ids == [collection_id]


def test_folder_readiness_warns_when_collection_is_weak():
    diagnostics = folders._readiness_from_counts(
        paper_count=2,
        full_text_count=0,
        embedding_count=1,
        read_status_counts={"unread": 2, "reading": 0, "completed": 0},
    )

    assert diagnostics["ready_for_idea"] is False
    assert diagnostics["full_text_coverage"] == 0
    assert any("少于 3 篇" in warning for warning in diagnostics["warnings"])


def test_personal_collection_delete_remains_available_to_authenticated_users():
    dependencies = _dependency_calls("/api/papers/{paper_id}", "DELETE")

    assert get_current_user in dependencies
    assert require_admin not in dependencies
