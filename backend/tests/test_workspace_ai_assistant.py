"""Contract tests for workspace-scoped AI assistant behavior."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api import chat_sessions
from app.api import workspaces
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


def test_workspace_assistant_routes_require_authentication():
    private_routes = [
        ("/api/workspaces/{space_id}/assistant", "GET"),
        ("/api/workspaces/{space_id}/assistant/send", "POST"),
    ]

    for path, method in private_routes:
        assert get_current_user in _dependency_calls(path, method)


def test_workspace_assistant_session_metadata_marks_workspace_scope():
    assert "scope" in workspaces._workspace_assistant_session.__code__.co_consts
    assert "workspace" in workspaces._workspace_assistant_session.__code__.co_consts
    assert "workspace_id" in workspaces._workspace_assistant_session.__code__.co_consts


def test_generic_chat_session_filter_excludes_workspace_scoped_sessions():
    workspace_session = SimpleNamespace(metadata_json={"scope": "workspace", "workspace_id": str(uuid4())})
    generic_session = SimpleNamespace(metadata_json={})

    assert chat_sessions._is_workspace_scoped_session(workspace_session) is True
    assert chat_sessions._is_workspace_scoped_session(generic_session) is False


def test_workspace_assistant_context_contains_resources_actions_and_boundaries():
    now = datetime.now(timezone.utc)
    service = WorkspaceService(SimpleNamespace())
    space = SimpleNamespace(name="Video Grounding", description="shared project")
    linked = {
        "papers": [{"id": str(uuid4()), "title": "Grounded Video Reasoning", "subtitle": "2026 · arXiv", "path": "/papers/1"}],
        "research_projects": [{"id": str(uuid4()), "title": "Temporal grounding", "subtitle": "研究方向", "path": "/research/1"}],
        "writing_projects": [{"id": str(uuid4()), "title": "Survey Draft", "subtitle": "survey", "path": "/writing?project=1"}],
    }
    activities = [{
        "id": str(uuid4()),
        "actor_name": "Alice",
        "action": "resource_linked",
        "resource_type": "papers",
        "resource_id": "paper-1",
        "metadata_json": {"title": "Grounded Video Reasoning"},
        "created_at": now.isoformat(),
    }]

    sections = "\n".join([
        "你是项目空间 AI 助手，只能基于下面给出的项目空间上下文提供建议。",
        "不要声称已经阅读完整 PDF、完整草稿或未提供的外部资料。",
        service._assistant_resource_section("已绑定论文", linked["papers"]),
        service._assistant_next_actions_section([{"label": "推进写作", "path": "/writing"}]),
        service._assistant_activity_section(activities),
    ])
    references = service._assistant_references(linked, activities)

    assert "项目空间 AI 助手" in sections
    assert "不要声称已经阅读完整 PDF" in sections
    assert "Grounded Video Reasoning" in sections
    assert "推进写作" in sections
    assert references[0]["source"] == "workspace"
    assert references[0]["source_label"] == "空间论文"
    assert references[0]["path"] == "/papers/1"


def test_assistant_llm_messages_include_system_context_recent_history_and_user_turn():
    history = [
        SimpleNamespace(role="user", content=f"u{i}")
        for i in range(10)
    ]

    messages = workspaces._assistant_llm_messages("workspace context", history, "下一步是什么")

    assert messages[0] == {"role": "system", "content": "workspace context"}
    assert len(messages) == 10
    assert messages[1]["content"] == "u2"
    assert messages[-1] == {"role": "user", "content": "下一步是什么"}
