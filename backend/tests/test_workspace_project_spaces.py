"""Regression tests for project spaces and workflow unification."""

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


def test_workspace_routes_require_authentication():
    private_routes = [
        ("/api/workspaces", "POST"),
        ("/api/workspaces", "GET"),
        ("/api/workspaces/resource-links", "GET"),
        ("/api/workspaces/{space_id}", "GET"),
        ("/api/workspaces/{space_id}", "PATCH"),
        ("/api/workspaces/{space_id}", "DELETE"),
        ("/api/workspaces/{space_id}/members", "POST"),
        ("/api/workspaces/{space_id}/members/candidates", "GET"),
        ("/api/workspaces/{space_id}/members/{user_id}", "DELETE"),
        ("/api/workspaces/{space_id}/activities", "GET"),
        ("/api/workspaces/{space_id}/resource-candidates", "GET"),
        ("/api/workspaces/{space_id}/resources", "POST"),
        ("/api/workspaces/{space_id}/resources/{resource_type}/{resource_id}", "DELETE"),
    ]

    for path, method in private_routes:
        assert get_current_user in _dependency_calls(path, method)


def test_workspace_role_and_next_actions_are_user_scoped():
    owner_id = uuid4()
    member_id = uuid4()
    now = datetime.now(timezone.utc)
    space = SimpleNamespace(
        id=uuid4(),
        owner_id=owner_id,
        name="Video Grounding Workspace",
        description="",
        status="active",
        metadata_json={},
        created_at=now,
        updated_at=now,
        members=[
            SimpleNamespace(user_id=owner_id, role="owner", created_at=now),
            SimpleNamespace(user_id=member_id, role="viewer", created_at=now),
        ],
    )
    service = WorkspaceService(SimpleNamespace())

    assert service._role_for(space, owner_id) == "owner"
    assert service._role_for(space, member_id) == "viewer"
    assert service._role_for(space, uuid4()) == "none"

    actions = service._next_actions({
        "counts": {
            "linked_papers": 0,
            "recent_papers": 0,
            "recent_research_projects": 0,
            "recent_writing_projects": 0,
        }
    })

    assert [action["kind"] for action in actions] == ["papers", "research", "writing"]


def test_workspace_resource_briefs_provide_module_paths():
    service = WorkspaceService(SimpleNamespace())
    paper_id = uuid4()
    research_id = uuid4()
    writing_id = uuid4()

    paper = SimpleNamespace(id=paper_id, title="Grounded Video Reasoning", year=2026, arxiv_id="2606.00001", source="arxiv")
    research = SimpleNamespace(id=research_id, name="Video Grounding", description="Temporal grounding")
    writing = SimpleNamespace(id=writing_id, title="Video Grounding Survey", description="", template_type="survey")

    assert service._paper_brief(paper)["path"] == f"/papers/{paper_id}"
    assert service._research_brief(research)["path"] == f"/research/{research_id}"
    assert service._writing_brief(writing)["path"] == f"/writing?project={writing_id}"


def test_workspace_resource_links_prefer_durable_links_and_keep_legacy_compatibility():
    now = datetime.now(timezone.utc)
    durable_id = uuid4()
    legacy_id = uuid4()
    space = SimpleNamespace(
        metadata_json={"resource_links": [
            {"type": "paper", "id": str(durable_id)},
            {"type": "research_project", "id": str(legacy_id)},
        ]},
        resources=[
            SimpleNamespace(
                id=uuid4(),
                resource_type="papers",
                resource_id=str(durable_id),
                added_by=uuid4(),
                created_at=now,
            )
        ],
    )
    service = WorkspaceService(SimpleNamespace())

    links = service._resource_links_from_space(space)

    assert links[0]["type"] == "papers"
    assert links[0].get("legacy") is None
    assert links[1]["type"] == "research_projects"
    assert links[1]["legacy"] is True
    assert len(links) == 2


def test_workspace_resource_type_aliases_are_normalized():
    service = WorkspaceService(SimpleNamespace())

    assert service._normalize_resource_type("paper") == "papers"
    assert service._normalize_resource_type("research_project") == "research_projects"
    assert service._normalize_resource_type("writing") == "writing_projects"
    assert service._normalize_resource_type("unknown") is None


def test_workspace_linked_resource_key_set_includes_durable_and_legacy_links():
    durable_id = uuid4()
    legacy_id = uuid4()
    now = datetime.now(timezone.utc)
    space = SimpleNamespace(
        metadata_json={"resource_links": [{"type": "writing_project", "id": str(legacy_id)}]},
        resources=[
            SimpleNamespace(
                id=uuid4(),
                resource_type="papers",
                resource_id=str(durable_id),
                added_by=uuid4(),
                created_at=now,
            )
        ],
    )
    service = WorkspaceService(SimpleNamespace())

    keys = service._linked_resource_key_set(space)

    assert ("papers", str(durable_id)) in keys
    assert ("writing_projects", str(legacy_id)) in keys


def test_workspace_resource_link_status_rows_mark_linked_and_editable_spaces():
    user_id = uuid4()
    resource_id = uuid4()
    now = datetime.now(timezone.utc)
    space = SimpleNamespace(
        id=uuid4(),
        name="Video Grounding",
        description="shared workspace",
        status="active",
        owner_id=user_id,
        metadata_json={},
        created_at=now,
        updated_at=now,
        members=[SimpleNamespace(user_id=user_id, role="editor", created_at=now)],
        resources=[
            SimpleNamespace(
                id=uuid4(),
                resource_type="papers",
                resource_id=str(resource_id),
                added_by=user_id,
                created_at=now,
            )
        ],
    )
    service = WorkspaceService(SimpleNamespace())

    row = {
        "id": str(space.id),
        "name": space.name,
        "role": service._role_for(space, user_id),
        "linked": ("papers", str(resource_id)) in service._linked_resource_key_set(space),
        "can_edit": service._role_for(space, user_id) in {"owner", "editor"},
    }

    assert row["linked"] is True
    assert row["can_edit"] is True
    assert row["role"] == "editor"


def test_workspace_activity_records_include_actor_resource_and_metadata():
    added = []
    session = SimpleNamespace(add=lambda item: added.append(item))
    service = WorkspaceService(session)
    space = SimpleNamespace(id=uuid4())
    user = SimpleNamespace(id=uuid4())

    activity = service._record_activity(
        space,
        user,
        "resource_linked",
        resource_type="papers",
        resource_id=str(uuid4()),
        metadata={"title": "Grounded Video Reasoning"},
    )

    assert added == [activity]
    assert activity.space_id == space.id
    assert activity.actor_id == user.id
    assert activity.action == "resource_linked"
    assert activity.resource_type == "papers"
    assert activity.metadata_json["title"] == "Grounded Video Reasoning"


def test_workspace_member_candidate_marks_existing_members():
    service = WorkspaceService(SimpleNamespace())
    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        username="alice",
        email="alice@example.com",
        display_name="Alice",
        avatar=None,
        role="user",
    )

    candidate = service._member_candidate_dict(user, existing_role="editor")

    assert candidate["account"] == "alice"
    assert candidate["label"] == "Alice"
    assert candidate["is_member"] is True
    assert candidate["member_role"] == "editor"


def test_workspace_dashboard_stage_progress_and_status_cards():
    service = WorkspaceService(SimpleNamespace())

    empty_dashboard = service.build_dashboard({
        "counts": {
            "linked_papers": 0,
            "linked_research_projects": 0,
            "linked_writing_projects": 0,
            "recent_activities": 0,
        }
    })

    assert empty_dashboard["stage"] == "setup"
    assert empty_dashboard["stage_label"] == "待搭建"
    assert empty_dashboard["progress_score"] == 0
    assert empty_dashboard["status_cards"][0]["status"] == "empty"

    active_dashboard = service.build_dashboard({
        "counts": {
            "linked_papers": 2,
            "linked_research_projects": 1,
            "linked_writing_projects": 1,
            "recent_activities": 3,
        }
    })

    assert active_dashboard["stage"] == "drafting"
    assert active_dashboard["stage_label"] == "写作推进中"
    assert active_dashboard["progress_score"] == 92
    assert active_dashboard["resource_balance"] == {
        "papers": 2,
        "research_projects": 1,
        "writing_projects": 1,
        "activity": 3,
    }
    assert [card["status"] for card in active_dashboard["status_cards"]] == ["ready", "ready", "ready", "ready"]


@pytest.mark.asyncio
async def test_workspace_list_includes_launchpad_summary(monkeypatch):
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    space = SimpleNamespace(
        id=uuid4(),
        owner_id=user_id,
        name="Launchpad Workspace",
        description="",
        status="active",
        metadata_json={},
        created_at=now,
        updated_at=now,
        members=[SimpleNamespace(user_id=user_id, role="owner", created_at=now)],
        resources=[],
    )

    class _ScalarRows:
        def unique(self):
            return self

        def all(self):
            return [space]

    class _ExecuteResult:
        def scalars(self):
            return _ScalarRows()

    class _Session:
        async def execute(self, _query):
            return _ExecuteResult()

    service = WorkspaceService(_Session())

    async def _members_to_dict(_space):
        return [{"user_id": str(user_id), "role": "owner"}]

    async def _build_summary(_space):
        return {
            "linked_resources": {"papers": [], "research_projects": [], "writing_projects": []},
            "recent_resources": {"papers": [], "research_projects": [], "writing_projects": []},
            "counts": {
                "linked_papers": 2,
                "linked_research_projects": 1,
                "linked_writing_projects": 0,
                "recent_papers": 2,
                "recent_research_projects": 1,
                "recent_writing_projects": 0,
                "recent_activities": 1,
            },
        }

    async def _activities(_space, limit=20):
        return []

    async def _open_issue_summary(_space, limit=5):
        return []

    monkeypatch.setattr(service, "_members_to_dict", _members_to_dict)
    monkeypatch.setattr(service, "build_summary", _build_summary)
    monkeypatch.setattr(service, "recent_activities_for_space", _activities)
    monkeypatch.setattr(service, "_open_issue_summary", _open_issue_summary)

    rows = await service.list_spaces(SimpleNamespace(id=user_id))

    assert rows[0]["summary"]["counts"]["linked_papers"] == 2
    assert rows[0]["dashboard"]["stage"] == "researching"
    assert rows[0]["dashboard"]["progress_score"] > 0
    assert rows[0]["next_actions"]
