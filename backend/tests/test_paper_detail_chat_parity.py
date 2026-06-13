from types import SimpleNamespace
import asyncio

import pytest
from pydantic import ValidationError

from app.api import chat_sessions, papers
from app.services import memory_service


def test_ask_paper_request_validates_retrieval_depth():
    request = papers.AskPaperRequest(
        question="论文的方法有什么局限？",
        rag_enabled=False,
        web_search=True,
        search_depth="deep",
    )

    assert request.rag_enabled is False
    assert request.web_search is True
    assert request.search_depth == "deep"
    with pytest.raises(ValidationError):
        papers.AskPaperRequest(question="question", search_depth="unbounded")


def test_ask_paper_request_accepts_image_attachments_for_current_turn():
    request = papers.AskPaperRequest(
        question="请分析这张补充实验图",
        attachments=[
            chat_sessions.ChatImageAttachment(
                filename="result.png",
                mime_type="image/png",
                data_url="data:image/png;base64,aGVsbG8=",
            )
        ],
    )

    assert request.attachments[0].filename == "result.png"
    assert request.attachments[0].data_url.startswith("data:image/png;base64,")


def test_paper_chat_image_attachments_become_openai_vision_parts(monkeypatch):
    monkeypatch.setattr(
        chat_sessions.llm_service,
        "get_active_option",
        lambda: {"provider": chat_sessions.OPENAI_COMPATIBLE_PROVIDER},
    )
    request = papers.AskPaperRequest(
        question="请结合当前论文分析这张图",
        attachments=[
            chat_sessions.ChatImageAttachment(
                filename="figure.png",
                mime_type="image/png",
                data_url="data:image/png;base64,aGVsbG8=",
            )
        ],
    )
    context = [
        {"role": "system", "content": "paper context"},
        {"role": "user", "content": "请结合当前论文分析这张图"},
    ]

    result = chat_sessions._build_llm_context_for_request(context, request)

    assert result == [
        {"role": "system", "content": "paper context"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请结合当前论文分析这张图"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,aGVsbG8="}},
            ],
        },
    ]


@pytest.mark.asyncio
async def test_paper_chat_keeps_current_paper_and_appends_optional_retrieval(monkeypatch):
    calls = []
    paper = SimpleNamespace(title="Primary paper")

    async def _fake_build_paper_context(current_paper, question, history):
        calls.append(("paper", current_paper.title, question, history))
        return [{"role": "system", "content": "primary paper context"}], [
            {"title": current_paper.title, "source": "current_paper", "type": "paper_evidence", "id": "E1", "page": 2}
        ]

    async def _fake_append_retrieval_context(
        context,
        query,
        *,
        rag_enabled,
        web_search_enabled,
        search_depth,
    ):
        calls.append(("retrieval", query, rag_enabled, web_search_enabled, search_depth))
        context.insert(0, {"role": "system", "content": "online and related-paper context"})
        return [{"title": "Related paper", "arxiv_id": "2606.00001", "year": 2026, "similarity": 0.9}]

    monkeypatch.setattr(memory_service, "build_paper_context_with_evidence", _fake_build_paper_context)
    monkeypatch.setattr(chat_sessions, "_append_retrieval_context", _fake_append_retrieval_context)

    request = papers.AskPaperRequest(
        question="compare methods",
        history=[{"role": "user", "content": "history"}],
        rag_enabled=True,
        web_search=True,
        search_depth="deep",
    )
    context, references = await papers._build_paper_chat_context(paper, request)

    assert calls == [
        ("paper", "Primary paper", "compare methods", [{"role": "user", "content": "history"}]),
        ("retrieval", "compare methods", True, True, "deep"),
    ]
    assert context == [
        {"role": "system", "content": "online and related-paper context"},
        {"role": "system", "content": "primary paper context"},
    ]
    assert references[0]["type"] == "paper_evidence"
    assert references[0]["page"] == 2
    assert references[1]["title"] == "Related paper"


def test_paper_chat_metadata_event_preserves_references():
    event = chat_sessions._stream_event(
        "meta",
        {"references": [{"title": "Related paper", "arxiv_id": "2606.00001"}]},
    )

    assert '"type": "meta"' in event
    assert '"references"' in event


def test_paper_evidence_meta_reports_coverage_and_insufficient_state():
    assert papers._paper_evidence_meta([]) == {
        "evidence_count": 0,
        "visual_evidence_count": 0,
        "evidence_coverage": 0.0,
        "evidence_insufficient": True,
        "visual_evidence_available": False,
        "evidence_plan": None,
    }

    meta = papers._paper_evidence_meta([
        {"type": "paper_evidence", "id": "E1", "metadata": {"evidence_plan": {"intent": "experiment_analysis", "strategy": "experiment_complete"}}},
        {"type": "paper_evidence", "id": "E2"},
        {"title": "Related paper"},
    ])

    assert meta["evidence_count"] == 2
    assert meta["evidence_coverage"] == 0.6667
    assert meta["evidence_insufficient"] is False
    assert meta["evidence_plan"]["strategy"] == "experiment_complete"


@pytest.mark.asyncio
async def test_paper_context_requires_insufficient_evidence_disclosure():
    paper = SimpleNamespace(
        title="Abstract-only paper",
        authors=["A"],
        year=2026,
        abstract="Only an abstract is available.",
        full_text=None,
        arxiv_id=None,
        pdf_path=None,
    )

    context, evidence = await memory_service.build_paper_context_with_evidence(
        paper,
        "请介绍 introduction",
        history=[],
    )

    assert evidence == []
    assert "当前论文内容不足" in context[0]["content"]
    assert "不要根据摘要或常识补全" in context[0]["content"]


@pytest.mark.asyncio
async def test_paper_chat_recovers_visible_answer_after_reasoning_only_primary_stream(monkeypatch):
    calls = []

    async def _reasoning_only_stream(**kwargs):
        calls.append(("primary", kwargs["temperature"], kwargs["max_tokens"]))
        yield {"type": "reasoning", "content": "分析中"}
        raise RuntimeError("模型未返回可展示内容")

    async def _stable_content_stream(**kwargs):
        calls.append(("recovery", kwargs["temperature"], kwargs["max_tokens"], kwargs["messages"][-1]))
        yield "稳定回答"

    monkeypatch.setattr(papers.llm_service, "chat_stream_with_thinking", _reasoning_only_stream)
    monkeypatch.setattr(papers.llm_service, "chat_stream", _stable_content_stream)

    events = [
        event async for event in papers._stream_paper_answer_events(
            [{"role": "user", "content": "question"}],
            show_thinking=True,
            max_tokens=128000,
        )
    ]

    assert events == [
        {"type": "reasoning", "content": "分析中"},
        {"type": "status", "content": papers.PAPER_CHAT_RECOVERY_STATUS},
        {"type": "content", "content": "稳定回答"},
    ]
    assert calls[0][2] == 128000
    assert calls[1][2] == 128000
    assert calls[1][3] == {"role": "system", "content": papers.PAPER_CHAT_RECOVERY_PROMPT}


@pytest.mark.asyncio
async def test_paper_chat_skips_recovery_when_primary_stream_returns_content(monkeypatch):
    calls = []

    async def _content_stream(**kwargs):
        calls.append(("primary", kwargs["max_tokens"]))
        yield "直接回答"

    monkeypatch.setattr(papers.llm_service, "chat_stream", _content_stream)

    events = [
        event async for event in papers._stream_paper_answer_events(
            [{"role": "user", "content": "question"}],
            show_thinking=False,
            max_tokens=384000,
        )
    ]

    assert events == [{"type": "content", "content": "直接回答"}]
    assert calls == [("primary", 384000)]


@pytest.mark.asyncio
async def test_paper_chat_marks_late_stream_failure_without_error_content(monkeypatch):
    async def _interrupted_content_stream(**_kwargs):
        yield "已经生成的回答"
        raise RuntimeError("upstream disconnected")

    monkeypatch.setattr(papers.llm_service, "chat_stream", _interrupted_content_stream)

    events = [
        event async for event in papers._stream_paper_answer_events(
            [{"role": "user", "content": "question"}],
            show_thinking=False,
            max_tokens=128000,
        )
    ]

    assert events == [
        {"type": "content", "content": "已经生成的回答"},
        {"type": "warning", "content": papers.PAPER_CHAT_INTERRUPTED_WARNING},
    ]


@pytest.mark.asyncio
async def test_paper_chat_does_not_interrupt_slow_thinking_answer_after_content(monkeypatch):
    async def _slow_answer_stream(**_kwargs):
        yield {"type": "reasoning", "content": "分析中"}
        yield {"type": "content", "content": "第一段回答"}
        await asyncio.sleep(0.03)
        yield {"type": "content", "content": "，后续回答"}

    monkeypatch.setattr(papers, "PAPER_CHAT_PRIMARY_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(papers.llm_service, "chat_stream_with_thinking", _slow_answer_stream)

    events = [
        event async for event in papers._stream_paper_answer_events(
            [{"role": "user", "content": "question"}],
            show_thinking=True,
            max_tokens=128000,
        )
    ]

    assert events == [
        {"type": "reasoning", "content": "分析中"},
        {"type": "content", "content": "第一段回答"},
        {"type": "content", "content": "，后续回答"},
    ]


@pytest.mark.asyncio
async def test_paper_chat_recovers_visible_answer_after_thinking_timeout(monkeypatch):
    async def _stalled_reasoning_stream(**_kwargs):
        yield {"type": "reasoning", "content": "仍在分析"}
        await asyncio.sleep(0.05)
        yield {"type": "content", "content": "不应到达"}

    async def _stable_content_stream(**_kwargs):
        yield "超时后稳定回答"

    monkeypatch.setattr(papers, "PAPER_CHAT_PRIMARY_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(papers.llm_service, "chat_stream_with_thinking", _stalled_reasoning_stream)
    monkeypatch.setattr(papers.llm_service, "chat_stream", _stable_content_stream)

    events = [
        event async for event in papers._stream_paper_answer_events(
            [{"role": "user", "content": "question"}],
            show_thinking=True,
            max_tokens=128000,
        )
    ]

    assert events == [
        {"type": "reasoning", "content": "仍在分析"},
        {"type": "status", "content": papers.PAPER_CHAT_RECOVERY_STATUS},
        {"type": "content", "content": "超时后稳定回答"},
    ]


@pytest.mark.asyncio
async def test_clear_paper_chat_history_preserves_user_paper_state():
    from uuid import uuid4

    user_paper = SimpleNamespace(
        paper_chat_history=[{"role": "user", "content": "question"}],
        saved=True,
        personal_notes="keep notes",
        read_status="reading",
        personal_tags=["keep-tag"],
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
    response = await papers.clear_chat_history(str(uuid4()), db=db, user=SimpleNamespace(id=uuid4()))

    assert response == {"deleted": 1}
    assert user_paper.paper_chat_history == []
    assert user_paper.saved is True
    assert user_paper.personal_notes == "keep notes"
    assert user_paper.read_status == "reading"
    assert user_paper.personal_tags == ["keep-tag"]
    assert db.committed is True
