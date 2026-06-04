"""Regression tests for project spaces and workflow unification."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

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
        ("/api/workspaces/{space_id}", "GET"),
        ("/api/workspaces/{space_id}", "PATCH"),
        ("/api/workspaces/{space_id}", "DELETE"),
        ("/api/workspaces/{space_id}/members", "POST"),
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
