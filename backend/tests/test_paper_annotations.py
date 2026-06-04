"""Tests for personal PDF annotations on papers."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import papers


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _Db:
    def __init__(self, user_paper):
        self.user_paper = user_paper
        self.committed = False

    async def execute(self, _query):
        return _Result(self.user_paper)

    async def commit(self):
        self.committed = True

    def add(self, _item):
        self.user_paper = _item


@pytest.mark.asyncio
async def test_create_annotation_preserves_existing_user_paper_state():
    user_paper = SimpleNamespace(
        saved=False,
        read_status="reading",
        personal_notes="keep notes",
        personal_tags=["tag"],
        paper_chat_history=[{"role": "user", "content": "q"}],
        personal_annotations=[],
    )
    db = _Db(user_paper)

    response = await papers.create_paper_annotation(
        str(uuid4()),
        papers.PaperAnnotationRequest(text=" Important quote ", page=3),
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert response["text"] == "Important quote"
    assert response["page"] == 3
    assert user_paper.saved is True
    assert user_paper.read_status == "reading"
    assert user_paper.personal_notes == "keep notes"
    assert user_paper.personal_tags == ["tag"]
    assert user_paper.paper_chat_history == [{"role": "user", "content": "q"}]
    assert user_paper.personal_annotations == [response]
    assert db.committed is True


@pytest.mark.asyncio
async def test_list_annotations_returns_current_user_annotations():
    annotations = [{"id": "a1", "text": "quote", "page": 1, "kind": "quote", "created_at": "now"}]
    db = _Db(SimpleNamespace(personal_annotations=annotations))

    response = await papers.list_paper_annotations(
        str(uuid4()),
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert response == annotations


@pytest.mark.asyncio
async def test_delete_annotation_preserves_other_state():
    user_paper = SimpleNamespace(
        saved=True,
        read_status="completed",
        personal_notes="keep",
        paper_chat_history=[{"role": "assistant", "content": "a"}],
        personal_annotations=[
            {"id": "remove-me", "text": "old", "page": 1, "kind": "quote", "created_at": "now"},
            {"id": "keep-me", "text": "new", "page": 2, "kind": "quote", "created_at": "now"},
        ],
    )
    db = _Db(user_paper)

    response = await papers.delete_paper_annotation(
        str(uuid4()),
        "remove-me",
        db=db,
        user=SimpleNamespace(id=uuid4()),
    )

    assert response == {"deleted": True, "annotation_id": "remove-me"}
    assert user_paper.personal_annotations == [
        {"id": "keep-me", "text": "new", "page": 2, "kind": "quote", "created_at": "now"},
    ]
    assert user_paper.read_status == "completed"
    assert user_paper.personal_notes == "keep"
    assert user_paper.paper_chat_history == [{"role": "assistant", "content": "a"}]
    assert db.committed is True
