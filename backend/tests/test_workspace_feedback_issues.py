"""Contract tests for workspace feedback issues."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.security import get_current_user
from app.main import app
from app.services.workspace_service import WorkspaceService


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


def test_workspace_issue_routes_require_authentication():
    private_routes = [
        ("/api/workspaces/{space_id}/issues", "GET"),
        ("/api/workspaces/{space_id}/issues", "POST"),
        ("/api/workspaces/{space_id}/issues/{issue_id}", "GET"),
        ("/api/workspaces/{space_id}/issues/{issue_id}", "PATCH"),
        ("/api/workspaces/{space_id}/issues/{issue_id}/comments", "POST"),
    ]

    for path, method in private_routes:
        assert get_current_user in _dependency_calls(path, method)


def test_workspace_issue_normalizers_keep_tracker_values_stable():
    service = WorkspaceService(SimpleNamespace())

    assert service._normalize_issue_status("OPEN") == "open"
    assert service._normalize_issue_status("pending") is None
    assert service._normalize_issue_type("feature") == "idea"
    assert service._normalize_issue_type("problem") == "bug"
    assert service._normalize_issue_priority("urgent") == "urgent"
    assert service._normalize_issue_priority("blocker") is None
    assert service._normalize_issue_labels([" UI ", "ui", "Bug", ""]) == ["ui", "bug"]
    assert service._normalize_issue_resource_reference({
        "type": "paper",
        "id": "paper-1",
        "title": "  Grounded Agents  ",
        "path": "/papers/paper-1",
        "source_label": "资源反馈",
    }) == {
        "resource_type": "papers",
        "resource_id": "paper-1",
        "title": "Grounded Agents",
        "path": "/papers/paper-1",
        "source_label": "资源反馈",
    }
    assert service._normalize_issue_resource_reference({"type": "unknown", "id": "x"}) is None


def test_workspace_issue_activity_records_lifecycle_metadata():
    added = []
    session = SimpleNamespace(add=lambda item: added.append(item))
    service = WorkspaceService(session)
    space = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4())
    issue_id = uuid4()

    activity = service._record_activity(
        space,
        user,
        "issue_created",
        resource_type="issues",
        resource_id=str(issue_id),
        metadata={"title": "上传按钮太挤", "status": "open"},
    )

    assert added == [activity]
    assert activity.action == "issue_created"
    assert activity.resource_type == "issues"
    assert activity.resource_id == str(issue_id)
    assert activity.metadata_json["title"] == "上传按钮太挤"


def test_workspace_issue_notifications_target_other_members():
    added = []
    session = SimpleNamespace(add=lambda item: added.append(item))
    service = WorkspaceService(session)
    actor_id = uuid4()
    viewer_id = uuid4()
    space_id = uuid4()
    issue_id = uuid4()
    actor = SimpleNamespace(id=actor_id, display_name="Alice", username="alice")
    space = SimpleNamespace(
        id=space_id,
        name="Paper Workspace",
        members=[
            SimpleNamespace(user_id=actor_id, role="owner"),
            SimpleNamespace(user_id=viewer_id, role="viewer"),
        ],
    )
    issue = SimpleNamespace(id=issue_id, title="对话框排版问题", status="open")

    service._notify_issue_members(space, actor, issue, "issue_commented")

    assert len(added) == 1
    notification = added[0]
    assert str(notification.user_id) == str(viewer_id)
    assert notification.category == "workspace_issue"
    assert notification.metadata_json["path"] == f"/workspaces/{space_id}?issue={issue_id}"
    assert notification.metadata_json["action"] == "issue_commented"


@pytest.mark.asyncio
async def test_workspace_issue_serialization_includes_comments_and_author_names(monkeypatch):
    user_id = uuid4()
    issue_id = uuid4()
    now = datetime.now(timezone.utc)
    service = WorkspaceService(SimpleNamespace())
    user = SimpleNamespace(id=user_id, display_name="Alice", username="alice", email="alice@example.com")
    issue = SimpleNamespace(
        id=issue_id,
        space_id=uuid4(),
        title="对话框排版问题",
        description="当前上下文太拥挤",
        status="open",
        issue_type="feedback",
        priority="medium",
        labels=["ui"],
        creator_id=user_id,
        assignee_id=None,
        closed_by_id=None,
        closed_at=None,
        metadata_json={
            "resource_reference": {
                "resource_type": "papers",
                "resource_id": "paper-1",
                "title": "Grounded Agents",
                "path": "/papers/paper-1",
            }
        },
        comments=[
            SimpleNamespace(
                id=uuid4(),
                issue_id=issue_id,
                author_id=user_id,
                content="需要折叠上下文",
                created_at=now,
                updated_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )

    async def fake_users_by_id(_user_ids):
        return {user_id: user}

    monkeypatch.setattr(service, "_users_by_id", fake_users_by_id)

    result = await service.issue_to_dict(issue, include_comments=True)

    assert result["creator_name"] == "Alice"
    assert result["resource_reference"]["path"] == "/papers/paper-1"
    assert result["comment_count"] == 1
    assert result["comments"][0]["author_name"] == "Alice"
    assert result["comments"][0]["content"] == "需要折叠上下文"


def test_workspace_issue_summaries_feed_next_actions_and_assistant_context():
    service = WorkspaceService(SimpleNamespace())
    issue = {
        "id": "issue-1",
        "title": "修复图片上传",
        "issue_type": "bug",
        "priority": "high",
        "labels": ["ui"],
        "path": "/workspaces/space-1?issue=issue-1",
        "resource_reference": {
            "resource_type": "papers",
            "resource_id": "paper-1",
            "title": "Grounded Agents",
            "path": "/papers/paper-1",
        },
    }

    actions = service._next_actions({"counts": {}}, [issue])
    assert actions[0] == {
        "label": "处理 Issue：修复图片上传",
        "path": "/workspaces/space-1?issue=issue-1",
        "kind": "issue",
        "priority": "high",
    }

    issue_section = service._assistant_issue_section([issue])
    assert "开放反馈 Issue" in issue_section
    assert "修复图片上传" in issue_section
    assert "关联 papers Grounded Agents" in issue_section

    references = service._assistant_references({}, [], [issue])
    assert references == [{
        "source": "workspace",
        "source_label": "开放 Issue",
        "resource_type": "issues",
        "resource_id": "issue-1",
        "title": "修复图片上传",
        "path": "/workspaces/space-1?issue=issue-1",
    }]


@pytest.mark.asyncio
async def test_workspace_viewer_can_submit_comments_but_not_triage(monkeypatch):
    service = WorkspaceService(SimpleNamespace())
    user = SimpleNamespace(id=uuid4())
    space = SimpleNamespace(id=uuid4(), members=[SimpleNamespace(user_id=user.id, role="viewer")])

    async def fake_access(_space_id, _user):
        return space, "viewer"

    monkeypatch.setattr(service, "get_space_for_user", fake_access)

    with pytest.raises(PermissionError):
        await service.update_issue(str(space.id), str(uuid4()), user, status="closed")
