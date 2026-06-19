"""Contract tests for paper chat share discussion threads."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api import notifications
from app.core.security import get_current_user
from app.db.models.notification import (
    Notification,
    PaperChatShareComment,
    PaperChatShareParticipant,
    PaperChatShareStatus,
    PaperChatShareThread,
)
from app.main import app


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


def test_paper_chat_share_discussion_routes_require_authentication():
    private_routes = [
        ("/api/notifications/paper-chat-shares/{notification_id}/thread", "GET"),
        ("/api/notifications/paper-chat-shares/{notification_id}/comments", "POST"),
        ("/api/notifications/paper-chat-shares/{notification_id}/status", "PUT"),
    ]

    for path, method in private_routes:
        assert get_current_user in _dependency_calls(path, method)


def test_paper_chat_share_discussion_models_capture_thread_state():
    thread_id = uuid4()
    user_id = uuid4()
    notification_id = uuid4()

    thread = PaperChatShareThread(
        id=thread_id,
        paper_id=uuid4(),
        sender_id=user_id,
        title="Grounded Video Reasoning",
        metadata_json={"paper_title": "Grounded Video Reasoning"},
    )
    participant = PaperChatShareParticipant(
        thread_id=thread_id,
        user_id=user_id,
        role="sender",
        notification_id=notification_id,
    )
    comment = PaperChatShareComment(thread_id=thread_id, author_id=user_id, content="建议跟进实验设置")
    status = PaperChatShareStatus(thread_id=thread_id, user_id=user_id, status="follow_up")

    assert thread.title == "Grounded Video Reasoning"
    assert participant.role == "sender"
    assert participant.notification_id == notification_id
    assert comment.content == "建议跟进实验设置"
    assert status.status == "follow_up"


def test_paper_chat_share_discussion_notification_metadata_targets_digest_center():
    thread_id = uuid4()
    comment_id = uuid4()
    notification = Notification(
        user_id=uuid4(),
        title="Alice 回复了论文精读分享",
        content="《Grounded Video Reasoning》的精读分享有新评论。",
        category=notifications.PAPER_CHAT_SHARE_DISCUSSION_CATEGORY,
        metadata_json={
            "action": "paper_chat_share_commented",
            "share_thread_id": str(thread_id),
            "comment_id": str(comment_id),
            "path": "/papers/digests",
            "target_notification_id": str(uuid4()),
        },
    )

    assert notification.category == "paper_chat_share_discussion"
    assert notification.metadata_json["path"] == "/papers/digests"
    assert notification.metadata_json["share_thread_id"] == str(thread_id)


@pytest.mark.asyncio
async def test_legacy_share_notification_without_thread_gets_thread_metadata():
    user_id = uuid4()
    paper_id = uuid4()
    notification = Notification(
        id=uuid4(),
        user_id=user_id,
        title="Alice 分享了论文 AI 精读",
        content="分享了《Grounded Video Reasoning》中的 2 条论文问答片段。",
        category="paper_chat_share",
        metadata_json={
            "paper_id": str(paper_id),
            "paper_title": "Grounded Video Reasoning",
            "sender_id": str(user_id),
            "sender_name": "Alice",
            "path": f"/papers/{paper_id}",
        },
    )

    class Result:
        def __init__(self, value=None):
            self.value = value

        def scalar_one_or_none(self):
            return self.value

    class FakeSession:
        def __init__(self):
            self.added = []
            self.flushed = 0

        async def execute(self, _statement):
            return Result(None)

        def add(self, item):
            self.added.append(item)
            if getattr(item, "id", None) is None:
                item.id = uuid4()

        async def flush(self):
            self.flushed += 1

    session = FakeSession()
    thread = await notifications._ensure_share_thread_for_notification(session, notification)

    assert thread.id
    assert notification.metadata_json["share_thread_id"] == str(thread.id)
    assert any(isinstance(item, PaperChatShareParticipant) for item in session.added)


@pytest.mark.asyncio
async def test_comment_notifications_target_other_thread_participants():
    thread_id = uuid4()
    actor_id = uuid4()
    recipient_id = uuid4()
    sender_id = uuid4()
    thread = PaperChatShareThread(
        id=thread_id,
        sender_id=sender_id,
        title="Grounded Video Reasoning",
    )
    comment = PaperChatShareComment(id=uuid4(), thread_id=thread_id, author_id=actor_id, content="建议复现实验")
    actor = SimpleNamespace(id=actor_id, display_name="Alice", username="alice", email="alice@example.com")
    participants = [
        PaperChatShareParticipant(thread_id=thread_id, user_id=actor_id, role="recipient", notification_id=uuid4()),
        PaperChatShareParticipant(thread_id=thread_id, user_id=recipient_id, role="recipient", notification_id=uuid4()),
        PaperChatShareParticipant(thread_id=thread_id, user_id=sender_id, role="sender", notification_id=uuid4()),
    ]

    class Result:
        def scalars(self):
            return self

        def all(self):
            return participants

    class FakeSession:
        def __init__(self):
            self.added = []

        async def execute(self, _statement):
            return Result()

        def add(self, item):
            self.added.append(item)

    session = FakeSession()
    await notifications._notify_paper_chat_share_comment(session, thread, comment, actor)

    notified_ids = {item.user_id for item in session.added if isinstance(item, Notification)}
    assert recipient_id in notified_ids
    assert sender_id in notified_ids
    assert actor_id not in notified_ids


def test_invalid_share_status_request_is_rejected_by_schema():
    with pytest.raises(ValueError):
        notifications.PaperChatShareStatusRequest(status="ignored")


def test_empty_comment_request_is_rejected_by_schema():
    with pytest.raises(ValueError):
        notifications.PaperChatShareCommentRequest(content="")
