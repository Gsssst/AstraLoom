"""Tests for the personal paper reading workflow."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import papers


@pytest.mark.asyncio
async def test_reading_status_counts_returns_all_statuses():
    class _Result:
        def all(self):
            return [("unread", 2), ("completed", 1)]

    class _Db:
        async def execute(self, _query):
            return _Result()

    response = await papers.get_reading_status_counts(
        db=_Db(),
        user=SimpleNamespace(id=uuid4()),
    )

    assert response.unread == 2
    assert response.reading == 0
    assert response.completed == 1


@pytest.mark.asyncio
async def test_update_read_status_preserves_existing_personal_state():
    user_paper = SimpleNamespace(
        saved=False,
        read_status="unread",
        personal_notes="keep notes",
        personal_tags=["important"],
        paper_chat_history=[{"role": "user", "content": "question"}],
    )

    class _Result:
        def scalar_one_or_none(self):
            return user_paper

    class _Db:
        committed = False

        async def execute(self, _query):
            return _Result()

        async def commit(self):
            self.committed = True

    db = _Db()
    response = await papers.update_read_status(
        str(uuid4()),
        papers.ReadStatusRequest(status="reading"),
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert response == {"read_status": "reading", "saved": True}
    assert user_paper.saved is True
    assert user_paper.read_status == "reading"
    assert user_paper.personal_notes == "keep notes"
    assert user_paper.personal_tags == ["important"]
    assert user_paper.paper_chat_history == [{"role": "user", "content": "question"}]
    assert db.committed is True


@pytest.mark.asyncio
async def test_update_paper_importance_sets_and_clears_shared_marker():
    paper = SimpleNamespace(
        id=uuid4(),
        importance_label=None,
        importance_note=None,
    )

    class _Result:
        def scalar_one_or_none(self):
            return paper

    class _Db:
        committed = 0
        refreshed = 0

        async def execute(self, _query):
            return _Result()

        async def commit(self):
            self.committed += 1

        async def refresh(self, _paper):
            self.refreshed += 1

    db = _Db()

    marked = await papers.update_paper_importance(
        str(paper.id),
        papers.PaperImportanceRequest(label="important", note="Core baseline"),
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert marked.importance_label == "important"
    assert marked.importance_note == "Core baseline"
    assert paper.importance_label == "important"
    assert paper.importance_note == "Core baseline"

    cleared = await papers.update_paper_importance(
        str(paper.id),
        papers.PaperImportanceRequest(label=None, note="ignored"),
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert cleared.importance_label is None
    assert cleared.importance_note is None
    assert paper.importance_label is None
    assert paper.importance_note is None
    assert db.committed == 2
    assert db.refreshed == 2
