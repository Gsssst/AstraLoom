"""Contract tests for sharing paper AI chat insights to project-space members."""

from types import SimpleNamespace
from uuid import uuid4

from app.api import papers
from app.core.security import get_current_user
from app.db.models.notification import Notification
from app.db.models.workspace import ProjectSpaceActivity
from app.main import app


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


def test_paper_chat_share_routes_require_authentication():
    private_routes = [
        ("/api/papers/{paper_id}/share-targets", "GET"),
        ("/api/papers/{paper_id}/share-chat-insight", "POST"),
    ]

    for path, method in private_routes:
        assert get_current_user in _dependency_calls(path, method)


def test_paper_chat_share_target_response_exposes_workspace_membership():
    space = SimpleNamespace(
        id=uuid4(),
        name="Video Grounding",
        description="Shared reading",
        members=[SimpleNamespace(user_id=uuid4()), SimpleNamespace(user_id=uuid4())],
    )

    target = papers._paper_chat_share_target_response(space, "viewer")

    assert target.id == str(space.id)
    assert target.name == "Video Grounding"
    assert target.role == "viewer"
    assert target.member_count == 2
    assert target.can_share is True


def test_paper_chat_share_bounds_text_and_references():
    assert papers._bounded_text("abcdef", 4) == "abc…"

    references = [
        papers.PaperChatShareReference(
            id="ref-1",
            title="Long evidence reference",
            page=3,
            snippet="x" * 900,
            locator={"text": "y" * 500},
        )
    ]
    bounded = papers._bounded_share_references(references)

    assert len(bounded) == 1
    assert bounded[0]["page"] == 3
    assert len(bounded[0]["snippet"]) <= 500
    assert len(bounded[0]["locator"]["text"]) <= 160


def test_paper_chat_share_notification_metadata_targets_other_members_only():
    sender_id = uuid4()
    recipient_id = uuid4()
    activity_id = uuid4()
    paper_id = uuid4()
    space_id = uuid4()
    metadata = {
        "workspace_id": str(space_id),
        "workspace_name": "Shared Lab",
        "paper_id": str(paper_id),
        "paper_title": "Grounded Video Reasoning",
        "sender_id": str(sender_id),
        "sender_name": "Alice",
        "question": "这篇论文的核心贡献是什么？",
        "answer": "它提出了一个可复用的证据组织方式。",
        "answer_excerpt": "它提出了一个可复用的证据组织方式。",
        "note": "建议组会讨论",
        "references": [{"page": 3, "title": "Method"}],
        "reference_count": 1,
        "path": f"/papers/{paper_id}",
        "action": "paper_chat_shared",
        "activity_id": str(activity_id),
    }

    notification = Notification(
        user_id=recipient_id,
        title="Alice 分享了论文 AI 精读",
        content="项目空间「Shared Lab」中分享了《Grounded Video Reasoning》的 AI 问答精选。",
        category="paper_chat_share",
        metadata_json=metadata,
    )
    activity = ProjectSpaceActivity(
        space_id=space_id,
        actor_id=sender_id,
        action="paper_chat_shared",
        resource_type="papers",
        resource_id=str(paper_id),
        metadata_json={
            "title": "Grounded Video Reasoning",
            "question": "这篇论文的核心贡献是什么？",
            "answer_excerpt": "它提出了一个可复用的证据组织方式。",
            "path": f"/papers/{paper_id}",
            "reference_count": 1,
        },
    )

    assert notification.user_id == recipient_id
    assert str(notification.user_id) != str(sender_id)
    assert notification.category == "paper_chat_share"
    assert notification.metadata_json["path"] == f"/papers/{paper_id}"
    assert notification.metadata_json["action"] == "paper_chat_shared"
    assert activity.action == "paper_chat_shared"
    assert activity.resource_type == "papers"
    assert activity.resource_id == str(paper_id)
