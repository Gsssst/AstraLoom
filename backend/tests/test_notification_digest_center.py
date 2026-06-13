"""Regression tests for the usable in-app arXiv digest center."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException

from app.api import notifications
from app.db.models.notification import Notification
from app.services.digest_service import DigestService
from app.services.paper_search import ArxivSearchService, PaperResult
from app.tasks.celery_app import celery_app
from app.tasks import daily_digest


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return SimpleNamespace(all=lambda: self.value)

    def scalar(self):
        return self.value


class _Session:
    def __init__(self, value=None):
        self.value = value
        self.added = []
        self.committed = False

    async def execute(self, _statement):
        return _ScalarResult(self.value)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid4()

    async def commit(self):
        self.committed = True

    async def refresh(self, _value):
        return None


@pytest.mark.asyncio
async def test_subscription_rejects_active_push_without_keywords():
    session = _Session()
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(HTTPException) as error:
        await notifications.update_subscription(
            notifications.SubscriptionUpdate(keywords=[], push_enabled=True),
            user=user,
            db=session,
        )

    assert error.value.status_code == 400
    assert "关键词" in error.value.detail


@pytest.mark.asyncio
async def test_subscription_rejects_email_until_transport_is_configured():
    session = _Session()
    user = SimpleNamespace(id=uuid4())

    with pytest.raises(HTTPException) as error:
        await notifications.update_subscription(
            notifications.SubscriptionUpdate(email_enabled=True),
            user=user,
            db=session,
        )

    assert error.value.status_code == 400
    assert "邮箱推送暂未配置" in error.value.detail


@pytest.mark.asyncio
async def test_manual_test_push_creates_visible_notification_even_when_empty(monkeypatch):
    session = _Session()
    service = DigestService(session)
    user_id = uuid4()

    async def no_papers(_keywords, max_per_keyword=3, freshness_hours=None):
        assert max_per_keyword == 3
        assert freshness_hours is None
        return []

    monkeypatch.setattr(service, "fetch_daily_papers", no_papers)

    delivery = await service.dispatch_in_app_digest(
        user_id=user_id,
        keywords=["video grounding"],
        is_test=True,
        notify_on_empty=True,
    )

    assert delivery["delivered"] is True
    assert delivery["paper_count"] == 0
    assert len(session.added) == 1
    notification = session.added[0]
    assert isinstance(notification, Notification)
    assert notification.user_id == user_id
    assert notification.metadata_json["is_test"] is True
    assert "暂无相关新论文" in notification.content


@pytest.mark.asyncio
async def test_digest_notification_preserves_actionable_paper_metadata(monkeypatch):
    local_id = uuid4()
    local_paper = SimpleNamespace(
        id=local_id,
        title="Grounded Video Research",
        arxiv_id="2606.00001v1",
        doi=None,
        source="arxiv",
        metadata_json={},
    )
    session = _Session([local_paper])
    service = DigestService(session)

    async def one_paper(_keywords, max_per_keyword=3, freshness_hours=None):
        assert max_per_keyword == 3
        assert freshness_hours is None
        return [{
            "title": "Grounded Video Research",
            "arxiv_id": "2606.00001v1",
            "authors": ["Alice", "Bob"],
            "year": 2026,
            "abstract_snippet": "A structured digest preview.",
        }]

    async def fixed_summary(_keywords, _papers):
        return "digest summary"

    monkeypatch.setattr(service, "fetch_daily_papers", one_paper)
    monkeypatch.setattr(service, "generate_digest_from_papers", fixed_summary)

    await service.dispatch_in_app_digest(
        user_id=uuid4(),
        keywords=["video grounding"],
        is_test=True,
        notify_on_empty=True,
    )

    paper = session.added[0].metadata_json["papers"][0]
    assert paper["title"] == "Grounded Video Research"
    assert paper["arxiv_id"] == "2606.00001v1"
    assert paper["authors"] == ["Alice", "Bob"]
    assert paper["year"] == 2026
    assert paper["abstract_snippet"] == "A structured digest preview."
    assert paper["canonical_key"] == "arxiv:2606.00001"
    assert paper["in_library"] is True
    assert paper["local_paper_id"] == str(local_id)
    assert paper["recommendation_reasons"]


def test_arxiv_parser_preserves_precise_publication_timestamp():
    papers = ArxivSearchService._parse_entries("""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>https://arxiv.org/abs/2606.00001v1</id>
    <published>2026-06-03T01:02:03Z</published>
    <title>Grounded Video Research</title>
    <summary>Fresh work.</summary>
    <author><name>Alice</name></author>
  </entry>
</feed>""")

    assert papers[0].published_at == "2026-06-03T01:02:03Z"


@pytest.mark.asyncio
async def test_digest_fetch_deduplicates_multi_source_results_and_filters_stale_dated_papers(monkeypatch):
    session = _Session()
    service = DigestService(session)
    fresh_published_at = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    stale_published_at = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    async def fake_search(**_kwargs):
        return [
            PaperResult(
                title="Fresh Paper", authors=["Alice"], abstract="video grounding",
                year=2026, published_at=fresh_published_at, arxiv_id="2606.00001v1",
                metadata={"remote_id": "2606.00001v1"},
            ),
            PaperResult(
                title="Fresh Paper", authors=["Alice"], abstract="duplicate",
                year=2026, published_at=fresh_published_at, arxiv_id="2606.00001v2",
                metadata={"remote_id": "2606.00001v2"},
            ),
            PaperResult(
                title="Stale Paper", authors=["Bob"], abstract="old",
                year=2026, published_at=stale_published_at, arxiv_id="2601.00001v1",
                metadata={"remote_id": "2601.00001v1"},
            ),
        ]

    monkeypatch.setattr("app.services.digest_service.search_scholarly_papers", fake_search)

    papers = await service.fetch_daily_papers(["video grounding"], freshness_hours=72)

    assert [paper["title"] for paper in papers] == ["Fresh Paper"]
    assert papers[0]["canonical_key"] == "arxiv:2606.00001"


@pytest.mark.asyncio
async def test_digest_ranker_suppresses_dismissed_paper_and_explains_project_match(monkeypatch):
    service = DigestService(_Session())

    async def fake_signals(_user_id):
        return {
            "profile_terms": {"grounding"},
            "interest_terms": set(),
            "dismissed_keys": {"arxiv:2606.00002"},
            "positive_keys": set(),
        }

    monkeypatch.setattr(service, "_collect_preference_signals", fake_signals)
    ranked = await service.rank_papers(
        user_id=uuid4(),
        keywords=["video grounding"],
        papers=[
            {"title": "Video Grounding", "canonical_key": "arxiv:2606.00001", "published_at": "2026-06-03T00:00:00Z", "source": "arxiv"},
            {"title": "Dismissed", "canonical_key": "arxiv:2606.00002", "source": "arxiv"},
        ],
    )

    assert [paper["canonical_key"] for paper in ranked] == ["arxiv:2606.00001"]
    assert "符合活跃研究方向" in ranked[0]["recommendation_reasons"]


@pytest.mark.asyncio
async def test_mark_all_digests_read_does_not_touch_unrelated_notifications():
    digest = SimpleNamespace(category="digest", is_read=False)
    system = SimpleNamespace(category="system", is_read=False)
    session = _Session([digest])

    result = await notifications.mark_all_digests_read(
        user=SimpleNamespace(id=uuid4()),
        db=session,
    )

    assert result == {"read_all": True, "updated": 1}
    assert digest.is_read is True
    assert system.is_read is False
    assert session.committed is True


@pytest.mark.asyncio
async def test_notification_list_can_filter_workspace_issue_category():
    workspace_issue = SimpleNamespace(
        id=uuid4(),
        title="Issue 新评论",
        content="Alice 评论了 Issue",
        category="workspace_issue",
        is_read=False,
        metadata_json={"path": "/workspaces/space-1?issue=issue-1"},
        created_at=datetime(2026, 6, 7),
    )
    session = _Session([workspace_issue])

    result = await notifications.list_notifications(
        limit=10,
        unread_only=False,
        category="workspace_issue",
        user=SimpleNamespace(id=uuid4()),
        db=session,
    )

    assert result == [{
        "id": str(workspace_issue.id),
        "title": "Issue 新评论",
        "content": "Alice 评论了 Issue",
        "category": "workspace_issue",
        "is_read": False,
        "metadata": {"path": "/workspaces/space-1?issue=issue-1"},
        "created_at": "2026-06-07T00:00:00",
    }]


@pytest.mark.asyncio
async def test_mark_all_read_can_scope_to_workspace_issue_category():
    workspace_issue = SimpleNamespace(category="workspace_issue", is_read=False)
    session = _Session([workspace_issue])

    result = await notifications.mark_all_read(
        category="workspace_issue",
        user=SimpleNamespace(id=uuid4()),
        db=session,
    )

    assert result == {"read_all": True, "updated": 1}
    assert workspace_issue.is_read is True
    assert session.committed is True


@pytest.mark.asyncio
async def test_digest_feedback_endpoint_persists_owned_paper_action():
    notification = SimpleNamespace(metadata_json={"feedback": {}}, category="digest")
    session = _Session(notification)

    result = await notifications.update_digest_feedback(
        str(uuid4()),
        notifications.DigestPaperFeedbackRequest(
            paper_key="arxiv:2606.00001",
            action="dismissed",
        ),
        user=SimpleNamespace(id=uuid4()),
        db=session,
    )

    assert result == {"paper_key": "arxiv:2606.00001", "action": "dismissed"}
    assert notification.metadata_json["feedback"]["arxiv:2606.00001"]["action"] == "dismissed"
    assert session.committed is True


@pytest.mark.asyncio
async def test_manual_test_endpoint_uses_saved_keywords_and_updates_delivery_time(monkeypatch):
    subscription = SimpleNamespace(
        keywords=["multimodal model"],
        last_sent_at=None,
    )
    session = _Session(subscription)
    user = SimpleNamespace(id=uuid4())
    calls = []

    async def fake_dispatch(self, **kwargs):
        calls.append(kwargs)
        return {
            "delivered": True,
            "notification_id": str(uuid4()),
            "paper_count": 1,
            "keywords": kwargs["keywords"],
            "message": "ok",
            "sent_at": "2026-06-02T08:00:00+00:00",
        }

    monkeypatch.setattr(DigestService, "dispatch_in_app_digest", fake_dispatch)

    result = await notifications.test_subscription(user=user, db=session)

    assert calls == [{
        "user_id": user.id,
        "keywords": ["multimodal model"],
        "is_test": True,
        "notify_on_empty": True,
    }]
    assert result["paper_count"] == 1
    assert subscription.last_sent_at is not None
    assert session.committed is True


@pytest.mark.asyncio
async def test_daily_digest_only_dispatches_due_subscription_hour(monkeypatch):
    due_user = uuid4()
    skipped_user = uuid4()
    subscriptions = [
        SimpleNamespace(user_id=due_user, keywords=["video grounding"], push_enabled=True, frequency="daily", send_hour=9, last_sent_at=None),
        SimpleNamespace(user_id=skipped_user, keywords=["llm"], push_enabled=True, frequency="daily", send_hour=8, last_sent_at=None),
    ]
    session = _Session(subscriptions)
    calls = []

    class _SessionFactory:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_args):
            return None

    async def fake_dispatch(self, **kwargs):
        calls.append(kwargs)
        return {"delivered": True}

    monkeypatch.setattr(daily_digest, "AsyncSessionLocal", lambda: _SessionFactory())
    monkeypatch.setattr(DigestService, "dispatch_in_app_digest", fake_dispatch)

    result = await daily_digest._run_digest(datetime(2026, 6, 5, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai")))

    assert result["due"] == 1
    assert result["notified"] == 1
    assert calls == [{"user_id": due_user, "keywords": ["video grounding"], "notify_on_empty": True}]
    assert subscriptions[0].last_sent_at.date().isoformat() == "2026-06-05"
    assert subscriptions[1].last_sent_at is None


@pytest.mark.asyncio
async def test_daily_digest_skips_subscription_already_sent_today(monkeypatch):
    subscription = SimpleNamespace(
        user_id=uuid4(),
        keywords=["video grounding"],
        push_enabled=True,
        frequency="daily",
        send_hour=9,
        last_sent_at=datetime(2026, 6, 5, 8, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    )
    session = _Session([subscription])
    calls = []

    class _SessionFactory:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_args):
            return None

    async def fake_dispatch(self, **kwargs):
        calls.append(kwargs)
        return {"delivered": True}

    monkeypatch.setattr(daily_digest, "AsyncSessionLocal", lambda: _SessionFactory())
    monkeypatch.setattr(DigestService, "dispatch_in_app_digest", fake_dispatch)

    result = await daily_digest._run_digest(datetime(2026, 6, 5, 9, 0, tzinfo=ZoneInfo("Asia/Shanghai")))

    assert result["due"] == 0
    assert result["notified"] == 0
    assert calls == []


def test_celery_registers_daily_digest_and_beijing_morning_schedule():
    assert "app.tasks.daily_digest" in celery_app.conf.include
    celery_app.loader.import_default_modules()
    assert "daily_arxiv_digest" in celery_app.tasks
    schedule = celery_app.conf.beat_schedule["daily-arxiv-digest"]
    assert schedule["task"] == "daily_arxiv_digest"
    assert str(schedule["schedule"]) == "<crontab: 0 * * * * (m/h/dM/MY/d)>"
