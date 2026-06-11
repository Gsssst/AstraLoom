"""管理员治理能力回归测试。"""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import admin as admin_api
from app.core.security import require_admin
from app.main import app


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class _CountSession:
    def __init__(self, count):
        self.count = count

    async def execute(self, _statement):
        return _ScalarResult(self.count)


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/admin/overview", "GET"),
        ("/api/admin/users", "GET"),
        ("/api/admin/users/{user_id}", "PATCH"),
        ("/api/admin/workspaces", "GET"),
        ("/api/admin/workspaces/{space_id}", "GET"),
        ("/api/admin/workspace-activities", "GET"),
    ],
)
def test_admin_routes_require_admin(path, method):
    assert require_admin in _dependency_calls(path, method)


@pytest.mark.asyncio
async def test_last_active_admin_cannot_be_removed():
    with pytest.raises(HTTPException) as error:
        await admin_api._ensure_not_last_admin(_CountSession(0), uuid4())

    assert error.value.status_code == 400
    assert "最后一个活跃管理员" in error.value.detail


@pytest.mark.asyncio
async def test_admin_safeguard_allows_changes_when_another_admin_exists():
    await admin_api._ensure_not_last_admin(_CountSession(1), uuid4())


@pytest.mark.asyncio
async def test_admin_workspace_detail_uses_admin_inspection_service(monkeypatch):
    expected = {"id": "space-1", "admin_view": True, "members": [], "summary": {}}

    async def fake_detail(self, space_id, admin):
        assert space_id == "space-1"
        assert admin.role == "admin"
        return expected

    monkeypatch.setattr(admin_api.WorkspaceService, "get_space_admin_detail", fake_detail)

    result = await admin_api.get_admin_workspace_detail(
        "space-1",
        db=SimpleNamespace(),
        admin=SimpleNamespace(role="admin"),
    )

    assert result is expected


@pytest.mark.asyncio
async def test_admin_workspace_detail_returns_404_for_missing_space(monkeypatch):
    async def fake_detail(self, space_id, admin):
        return None

    monkeypatch.setattr(admin_api.WorkspaceService, "get_space_admin_detail", fake_detail)

    with pytest.raises(HTTPException) as error:
        await admin_api.get_admin_workspace_detail(
            "missing",
            db=SimpleNamespace(),
            admin=SimpleNamespace(role="admin"),
        )

    assert error.value.status_code == 404


def test_workspace_role_counts_include_known_roles():
    space = SimpleNamespace(
        members=[
            SimpleNamespace(role="owner"),
            SimpleNamespace(role="editor"),
            SimpleNamespace(role="viewer"),
            SimpleNamespace(role="viewer"),
        ]
    )

    assert admin_api._workspace_role_counts(space) == {
        "owner": 1,
        "editor": 1,
        "viewer": 2,
    }


def test_overview_risk_hints_warn_about_single_admin():
    hints = admin_api._overview_risk_hints({"admins": 1, "project_spaces": 0})

    assert any("管理员" in hint for hint in hints)
    assert any("项目空间" in hint for hint in hints)
