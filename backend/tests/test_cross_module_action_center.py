"""Regression tests for the cross-module action center."""

from types import SimpleNamespace

from app.core.security import get_current_user
from app.main import app
from app.services.workflow_action_service import WorkflowActionService


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


def test_workflow_actions_route_requires_authentication():
    assert get_current_user in _dependency_calls("/api/workflow/actions", "GET")


def test_workflow_action_response_groups_and_sorts_by_priority():
    service = WorkflowActionService(SimpleNamespace())
    response = service.build_response([
        service.action(
            "writing:draft",
            "writing",
            "low",
            "继续写作",
            "补全草稿",
            "/writing",
            "writing-workflow",
        ),
        service.action(
            "papers:full-text",
            "papers",
            "high",
            "补全文",
            "提升论文问答证据覆盖",
            "/settings",
            "knowledge-maintenance",
        ),
        service.action(
            "research:ideas",
            "research",
            "medium",
            "评审 Idea",
            "检查草稿 idea",
            "/research",
            "idea-review",
        ),
    ])

    assert response["summary"] == {
        "total": 3,
        "high_priority": 1,
        "groups": {"papers": 1, "research": 1, "writing": 1},
    }
    assert [item["id"] for item in response["actions"]] == [
        "papers:full-text",
        "research:ideas",
        "writing:draft",
    ]


def test_workflow_action_can_describe_executable_maintenance():
    service = WorkflowActionService(SimpleNamespace())
    action = service.action(
        "papers:full-text",
        "papers",
        "high",
        "补全文",
        "提升论文问答证据覆盖",
        "/settings",
        "knowledge-maintenance",
        {"count": 7},
        action_type="api",
        action_label="补 5 篇全文",
        method="POST",
        endpoint="/papers/maintenance/backfill-full-text?limit=5",
        requires_admin=True,
    )

    assert action["action_type"] == "api"
    assert action["action_label"] == "补 5 篇全文"
    assert action["method"] == "POST"
    assert action["endpoint"] == "/papers/maintenance/backfill-full-text?limit=5"
    assert action["requires_admin"] is True
    assert action["path"] == "/settings"
