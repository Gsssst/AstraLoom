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
        ("/api/notifications/paper-chat-shares/{notification_id}/save-to-note", "POST"),
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


@pytest.mark.asyncio
async def test_save_discussion_to_note_rejects_share_without_local_paper(monkeypatch):
    user = SimpleNamespace(id=uuid4(), display_name="Alice", username="alice", email="alice@example.com")
    notification = Notification(id=uuid4(), user_id=user.id, title="分享", category="paper_chat_share")
    thread = PaperChatShareThread(id=uuid4(), paper_id=None, sender_id=user.id, title="Remote only paper")

    async def fake_owned_notification(_notification_id, _user, _db):
        return notification

    async def fake_ensure_thread(_db, _notification):
        return thread

    async def fake_assert_participant(_db, _thread_id, _user_id):
        return PaperChatShareParticipant(thread_id=thread.id, user_id=user.id, role="recipient")

    monkeypatch.setattr(notifications, "_owned_paper_chat_share_notification", fake_owned_notification)
    monkeypatch.setattr(notifications, "_ensure_share_thread_for_notification", fake_ensure_thread)
    monkeypatch.setattr(notifications, "_assert_thread_participant", fake_assert_participant)

    with pytest.raises(HTTPException) as exc:
        await notifications.save_paper_chat_share_discussion_to_note("share-id", user=user, db=SimpleNamespace())

    assert exc.value.status_code == 400
    assert "没有绑定本地论文" in exc.value.detail


@pytest.mark.asyncio
async def test_share_discussion_note_block_formats_messages_comments_and_statuses():
    user_id = uuid4()
    paper_id = uuid4()
    thread_id = uuid4()
    notification = Notification(
        id=uuid4(),
        user_id=user_id,
        title="Alice 分享了论文 AI 精读",
        content="分享了论文问答片段。",
        category="paper_chat_share",
        metadata_json={
            "paper_id": str(paper_id),
            "paper_title": "Grounded Video Reasoning",
            "sender_name": "Alice",
            "note": "建议组会讨论",
            "path": f"/papers/{paper_id}",
            "selected_messages": [
                {"role": "user", "content": "这篇论文的核心贡献是什么？"},
                {"role": "assistant", "content": "核心贡献是更稳健的视频定位。"},
            ],
        },
    )
    thread = PaperChatShareThread(
        id=thread_id,
        paper_id=paper_id,
        sender_id=user_id,
        title="Grounded Video Reasoning",
    )
    comment = PaperChatShareComment(id=uuid4(), thread_id=thread_id, author_id=user_id, content="补充消融实验")
    status = PaperChatShareStatus(thread_id=thread_id, user_id=user_id, status="useful")
    participant = PaperChatShareParticipant(thread_id=thread_id, user_id=user_id, role="sender")
    actor = SimpleNamespace(id=user_id, display_name="Alice", username="alice", email="alice@example.com")

    class Result:
        def __init__(self, values):
            self.values = values

        def scalars(self):
            return self

        def all(self):
            return self.values

    class FakeSession:
        async def execute(self, statement):
            text = str(statement)
            if "paper_chat_share_comments" in text:
                return Result([comment])
            if "paper_chat_share_statuses" in text:
                return Result([status])
            if "paper_chat_share_participants" in text:
                return Result([participant])
            if "users" in text:
                return Result([actor])
            return Result([])

    block, saved_at = await notifications._format_paper_chat_share_note_block(
        FakeSession(),
        notification=notification,
        thread=thread,
        current_user=actor,
    )

    assert saved_at
    assert "## 精读分享沉淀：Grounded Video Reasoning" in block
    assert "建议组会讨论" in block
    assert "这篇论文的核心贡献是什么？" in block
    assert "核心贡献是更稳健的视频定位。" in block
    assert "补充消融实验" in block
    assert "Alice: 有用" in block
    assert str(thread_id) in block


@pytest.mark.asyncio
async def test_get_or_create_user_paper_note_preserves_existing_note():
    existing = SimpleNamespace(user_id=uuid4(), paper_id=uuid4(), saved=False, personal_notes="已有笔记")

    class Result:
        def scalar_one_or_none(self):
            return existing

    class FakeSession:
        async def execute(self, _statement):
            return Result()

        def add(self, _item):
            raise AssertionError("existing user paper should not be recreated")

    user_paper = await notifications._get_or_create_user_paper_note(FakeSession(), existing.user_id, existing.paper_id)

    assert user_paper is existing
    assert user_paper.personal_notes == "已有笔记"
