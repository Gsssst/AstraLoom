"""Workspace-linked resource access control regression tests."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import research as research_api
from app.services.workspace_service import WorkspaceService


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _ProjectSession:
    def __init__(self, project):
        self.project = project

    async def execute(self, _statement):
        return _ScalarResult(self.project)


class _WorkspaceViewer:
    def __init__(self, _session):
        pass

    async def resource_role_for_user(self, *_args, **_kwargs):
        return "viewer"

    def role_can_read_resource(self, role):
        return role in {"viewer", "editor", "owner"}

    def role_can_edit_resource(self, role):
        return role in {"editor", "owner"}


def test_workspace_resource_roles_define_read_and_edit_boundary():
    service = WorkspaceService(SimpleNamespace())

    assert service.role_can_read_resource("viewer") is True
    assert service.role_can_read_resource("none") is False
    assert service.role_can_edit_resource("viewer") is False
    assert service.role_can_edit_resource("editor") is True
    assert service.role_can_edit_resource("owner") is True


@pytest.mark.asyncio
async def test_workspace_viewer_can_read_linked_research_project(monkeypatch):
    project = SimpleNamespace(id=uuid4(), user_id=uuid4(), ideas=[])
    user = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(research_api, "WorkspaceService", _WorkspaceViewer)

    result = await research_api._get_workspace_accessible_project(
        _ProjectSession(project),
        str(project.id),
        user,
    )

    assert result is project


@pytest.mark.asyncio
async def test_workspace_viewer_cannot_mutate_linked_research_project(monkeypatch):
    project = SimpleNamespace(id=uuid4(), user_id=uuid4(), ideas=[])
    user = SimpleNamespace(id=uuid4())
    monkeypatch.setattr(research_api, "WorkspaceService", _WorkspaceViewer)

    with pytest.raises(HTTPException) as error:
        await research_api._get_workspace_accessible_project(
            _ProjectSession(project),
            str(project.id),
            user,
            require_editor=True,
        )

    assert error.value.status_code == 403
