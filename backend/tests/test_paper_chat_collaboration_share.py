"""Contract tests for sharing paper AI chat insights to project-space members."""

import pytest
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
        ("/api/papers/{paper_id}/share-recipients", "GET"),
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


def test_paper_chat_share_recipient_response_uses_display_identity():
    user = SimpleNamespace(
        id=uuid4(),
        username="alice",
        email="alice@example.com",
        display_name="Alice Lab",
        avatar=None,
    )

    response = papers._paper_chat_share_recipient_response(user)

    assert response.id == str(user.id)
    assert response.label == "Alice Lab"
    assert response.email == "alice@example.com"


def test_paper_chat_share_bounds_selected_messages_with_references():
    selected = [
        papers.PaperChatShareSelectedMessage(
            role="user",
            content="请解释核心创新",
            message_index=1,
        ),
        papers.PaperChatShareSelectedMessage(
            role="assistant",
            content="a" * 7000,
            display_content="回答摘要",
            message_index=2,
            references=[
                papers.PaperChatShareReference(id="E1", title="Method", page=4, snippet="x" * 900),
            ],
        ),
    ]

    bounded = papers._bounded_share_selected_messages(selected)

    assert len(bounded) == 2
    assert bounded[0]["role"] == "user"
    assert bounded[1]["message_index"] == 2
    assert len(bounded[1]["content"]) <= 5000
    assert bounded[1]["reference_count"] == 1
    assert len(bounded[1]["references"][0]["snippet"]) <= 500


def test_paper_chat_share_request_accepts_all_users_flag():
    request = papers.PaperChatShareRequest(
        all_users=True,
        selected_messages=[
            papers.PaperChatShareSelectedMessage(role="user", content="请分享这段问题"),
        ],
    )

    assert request.all_users is True
    assert request.recipient_user_ids == []


@pytest.mark.asyncio
async def test_paper_chat_share_rejects_invalid_recipient_ids():
    sender_id = uuid4()

    with pytest.raises(papers.HTTPException) as exc_info:
        await papers._paper_chat_share_recipients_by_id(
            SimpleNamespace(),
            ["not-a-uuid"],
            sender_id,
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_paper_chat_share_all_recipients_excludes_sender():
    sender_id = uuid4()
    active_recipient = SimpleNamespace(id=uuid4())

    class FakeResult:
        def scalars(self):
            return self

        def all(self):
            return [active_recipient]

    class FakeSession:
        async def execute(self, statement):
            self.statement = statement
            return FakeResult()

    recipients = await papers._all_paper_chat_share_recipients(FakeSession(), sender_id)

    assert recipients == [active_recipient]


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


def test_paper_chat_direct_share_notification_metadata_contains_selected_messages():
    sender_id = uuid4()
    recipient_id = uuid4()
    paper_id = uuid4()
    selected_messages = [
        {"role": "user", "content": "这篇论文解决什么问题？", "excerpt": "这篇论文解决什么问题？", "message_index": 0},
        {"role": "assistant", "content": "它解决视频定位中的监督成本问题。", "excerpt": "它解决视频定位中的监督成本问题。", "message_index": 1},
    ]
    metadata = {
        "paper_id": str(paper_id),
        "paper_title": "Grounded Video Reasoning",
        "sender_id": str(sender_id),
        "sender_name": "Alice",
        "selected_messages": selected_messages,
        "message_count": len(selected_messages),
        "note": "建议讨论",
        "path": f"/papers/{paper_id}",
        "action": "paper_chat_shared",
        "recipient_mode": "all_users",
    }

    notification = Notification(
        user_id=recipient_id,
        title="Alice 分享了论文 AI 精读",
        content="分享了《Grounded Video Reasoning》中的 2 条论文问答片段。",
        category="paper_chat_share",
        metadata_json=metadata,
    )

    assert notification.user_id == recipient_id
    assert notification.metadata_json["recipient_mode"] == "all_users"
    assert notification.metadata_json["message_count"] == 2
    assert notification.metadata_json["selected_messages"][0]["role"] == "user"
