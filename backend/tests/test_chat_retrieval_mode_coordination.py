from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.api import chat_sessions
from app.services.web_search import WebSearchResult


class _AsyncContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def test_send_message_request_validates_search_depth():
    request = chat_sessions.SendMessageRequest(content="分析最新研究", search_depth="deep")

    assert request.search_depth == "deep"
    with pytest.raises(ValidationError):
        chat_sessions.SendMessageRequest(content="分析最新研究", search_depth="unbounded")


def test_paper_discovery_prompts_auto_route_to_research_scout():
    request = chat_sessions.SendMessageRequest(
        content="请帮我找10篇2025年到2026年发表的关于 video grounding 的 CVPR 论文",
        assistant_mode="general",
    )

    assert chat_sessions._is_paper_discovery_request(request.content) is True
    assert chat_sessions._effective_assistant_mode(request) == "research_scout"


def test_general_discussion_does_not_auto_route_to_research_scout():
    request = chat_sessions.SendMessageRequest(
        content="请解释一下 video grounding 这个任务通常怎么做",
        assistant_mode="general",
    )

    assert chat_sessions._is_paper_discovery_request(request.content) is False
    assert chat_sessions._effective_assistant_mode(request) == "general"


def test_research_scout_disables_generic_web_retrieval_even_when_web_search_requested():
    request = chat_sessions.SendMessageRequest(
        content="find 10 CVPR 2025 video grounding papers",
        web_search=True,
        assistant_mode="general",
    )

    effective_mode = chat_sessions._effective_assistant_mode(request)

    assert effective_mode == "research_scout"
    assert chat_sessions._web_search_enabled_for_mode(request, effective_mode) is False


def test_general_mode_keeps_requested_web_retrieval():
    request = chat_sessions.SendMessageRequest(
        content="请介绍一下 OpenAI API 的最新文档",
        web_search=True,
        assistant_mode="general",
    )

    effective_mode = chat_sessions._effective_assistant_mode(request)

    assert effective_mode == "general"
    assert chat_sessions._web_search_enabled_for_mode(request, effective_mode) is True


def test_research_scout_fallback_queries_expand_chinese_mllm_memory_prompt():
    intent = chat_sessions._research_scout_intent("请帮我找10篇关于多模态大模型memory的论文", "deep")

    queries = chat_sessions._fallback_research_scout_queries(
        "请帮我找10篇关于多模态大模型memory的论文",
        intent,
        limit=4,
    )

    assert "multimodal large language model memory" in queries
    assert any("MLLM" in query or "vision language model" in query for query in queries)
    assert all("请帮我" not in query and "论文" not in query for query in queries)


def test_research_scout_requested_count_overrides_depth_default():
    count_info = chat_sessions._research_scout_final_limit("请帮我找10篇关于 video grounding 的论文", "standard")

    assert count_info["requested_count"] == 10
    assert count_info["default_count"] == 8
    assert count_info["final_limit"] == 10
    assert count_info["capped"] is False


def test_research_scout_requested_count_is_capped_for_large_surveys():
    count_info = chat_sessions._research_scout_final_limit("请调研80篇关于 video grounding 的论文", "deep")

    assert count_info["requested_count"] == 80
    assert count_info["final_limit"] == chat_sessions.RESEARCH_SCOUT_MAX_FINAL_RESULTS
    assert count_info["capped"] is True


def test_research_scout_fallback_queries_expand_video_grounding_aliases():
    intent = chat_sessions._research_scout_intent("请帮我找10篇关于 video grounding 的论文", "deep")

    queries = chat_sessions._fallback_research_scout_queries(
        "请帮我找10篇关于 video grounding 的论文",
        intent,
        limit=8,
    )

    assert "video grounding" in queries
    assert "natural language video localization" in queries
    assert "temporal sentence grounding" in queries
    assert "text-to-video moment retrieval" in queries


def test_research_scout_planned_query_coercion_prefers_llm_queries_with_fallback():
    fallback = ["multimodal large language model memory", "MLLM memory"]

    queries = chat_sessions._coerce_research_scout_planned_queries(
        {"queries": ["memory augmented multimodal large language model", "vision language model memory"]},
        fallback,
        limit=3,
    )

    assert queries == [
        "memory augmented multimodal large language model",
        "vision language model memory",
        "multimodal large language model memory",
    ]


def test_research_scout_ranking_prefers_arxiv_pdf_but_keeps_broad_candidates():
    intent = chat_sessions._research_scout_intent("find multimodal memory papers", "deep")
    semantic = chat_sessions.PaperResult(
        title="Multimodal Large Language Model Memory",
        authors=["A"],
        abstract="multimodal large language model memory benchmark",
        year=2026,
        source="semantic_scholar",
        citation_count=900,
        metadata={"remote_id": "S1"},
    )
    arxiv = chat_sessions.PaperResult(
        title="Memory for Multimodal Agents",
        authors=["B"],
        abstract="multimodal memory model",
        year=2024,
        arxiv_id="2601.00001",
        source="arxiv",
        pdf_url="https://arxiv.org/pdf/2601.00001",
        citation_count=3,
        metadata={"remote_id": "2601.00001"},
    )

    ranked = chat_sessions._rank_research_scout_papers(
        [semantic, arxiv],
        "find multimodal memory papers",
        ["multimodal large language model memory"],
        intent,
        limit=2,
    )

    assert ranked[0].source == "arxiv"
    assert {paper.source for paper in ranked} == {"arxiv", "semantic_scholar"}


@pytest.mark.asyncio
async def test_research_scout_retrieval_falls_back_to_broad_scholarly_sources(monkeypatch):
    calls = []
    intent = chat_sessions._research_scout_intent("请帮我找10篇关于多模态大模型memory的论文", "deep")

    async def _fake_search_scholarly_papers(query, *, source, max_results, sort_by="relevance", **kwargs):
        calls.append((query, source, max_results, sort_by))
        if source == "arxiv_enriched":
            return []
        return [
            chat_sessions.PaperResult(
                title="Multimodal Large Language Model Memory",
                authors=["A"],
                abstract="multimodal large language model memory",
                year=2026,
                source="semantic_scholar",
                source_url="https://semanticscholar.org/paper/S1",
                citation_count=42,
                metadata={"remote_id": "S1"},
            ),
            chat_sessions.PaperResult(
                title="Memory Augmented Vision Language Models",
                authors=["B"],
                abstract="vision language model memory",
                year=2025,
                source="openalex",
                source_url="https://openalex.org/W1",
                pdf_url="https://example.com/paper.pdf",
                citation_count=12,
                metadata={"remote_id": "W1"},
            ),
        ]

    monkeypatch.setattr(chat_sessions, "search_scholarly_papers", _fake_search_scholarly_papers)

    papers, metadata = await chat_sessions._retrieve_research_scout_papers(
        "请帮我找10篇关于多模态大模型memory的论文",
        ["multimodal large language model memory"],
        intent,
        limit=10,
    )

    assert [call[1] for call in calls][:2] == ["arxiv_enriched", "scholarly"]
    assert any(call[1] == "scholarly" for call in calls[2:])
    assert metadata["fallback_used"] is True
    assert metadata["strategy"] == "arxiv_first_then_scholarly_fallback"
    assert metadata["stage_counts"]["arxiv_enriched"] == 0
    assert metadata["stage_counts"]["scholarly_fallback"] == 2
    assert {paper.source for paper in papers} == {"semantic_scholar", "openalex"}
    assert metadata["final_limit"] == 10
    assert metadata["pool_target"] > metadata["final_limit"]
    assert metadata["per_query_limit"] >= 12
    assert metadata["unique_pool_count"] == 2
    assert metadata["underfilled_by"] == 8


@pytest.mark.asyncio
async def test_research_scout_retrieval_uses_expanded_aliases_when_underfilled(monkeypatch):
    calls = []
    intent = chat_sessions._research_scout_intent("请帮我找10篇关于 video grounding 的论文", "deep")

    async def _fake_search_scholarly_papers(query, *, source, max_results, sort_by="relevance", **kwargs):
        calls.append((query, source, max_results, sort_by))
        if query == "video grounding" and source == "arxiv_enriched":
            return [
                chat_sessions.PaperResult(
                    title="Video Grounding Seed",
                    authors=["A"],
                    abstract="video grounding",
                    year=2025,
                    arxiv_id="2501.00001",
                    source="arxiv",
                    pdf_url="https://arxiv.org/pdf/2501.00001",
                    metadata={"remote_id": "2501.00001"},
                )
            ]
        if query == "natural language video localization" and source == "scholarly":
            return [
                chat_sessions.PaperResult(
                    title="Natural Language Video Localization",
                    authors=["B"],
                    abstract="natural language video localization",
                    year=2021,
                    source="openalex",
                    source_url="https://openalex.org/W1",
                    metadata={"remote_id": "W1"},
                )
            ]
        return []

    monkeypatch.setattr(chat_sessions, "search_scholarly_papers", _fake_search_scholarly_papers)

    papers, metadata = await chat_sessions._retrieve_research_scout_papers(
        "请帮我找10篇关于 video grounding 的论文",
        ["video grounding"],
        intent,
        limit=10,
        count_info={"requested_count": 10, "default_count": 8, "max_final_limit": 50, "capped": False},
    )

    assert {paper.title for paper in papers} == {"Video Grounding Seed", "Natural Language Video Localization"}
    assert "natural language video localization" in metadata["expanded_queries"]
    assert metadata["stage_counts"]["expanded_fallback"] == 1
    assert metadata["stage_counts"]["pool"] == 2
    assert metadata["underfilled_by"] == 8


def test_research_scout_tool_trace_reports_broad_fallback():
    trace = chat_sessions._research_scout_tool_trace(
        "请帮我找10篇关于多模态大模型memory的论文",
        {"topic": "多模态大模型memory"},
        [{"title": "Multimodal Large Language Model Memory", "evaluation": {"reading_priority": "high"}}],
        ["multimodal large language model memory"],
        {
            "strategy": "arxiv_first_then_scholarly_fallback",
            "fallback_used": True,
            "planned_queries": ["multimodal large language model memory"],
            "providers": ["Semantic Scholar", "OpenAlex"],
            "fallback_providers": ["Semantic Scholar", "OpenAlex"],
            "stage_counts": {"arxiv_enriched": 0, "scholarly_fallback": 2, "ranked": 1},
        },
    )

    search_step = next(step for step in trace["steps"] if step["tool"] == "search_papers")

    assert "扩展到 Semantic Scholar/OpenAlex/Google Scholar" in search_step["summary"]
    assert search_step["details"]["strategy"] == "arxiv_first_then_scholarly_fallback"
    assert search_step["details"]["fallback_used"] is True
    assert search_step["details"]["stage_counts"]["scholarly_fallback"] == 2


@pytest.mark.parametrize(
    ("search_depth", "expected"),
    [
        ("quick", {"rag_papers": 2, "web_results": 2, "web_queries": 1}),
        ("standard", {"rag_papers": 3, "web_results": 5, "web_queries": 3}),
        ("deep", {"rag_papers": 5, "web_results": 8, "web_queries": 5}),
        ("unknown", {"rag_papers": 3, "web_results": 5, "web_queries": 3}),
    ],
)
def test_retrieval_limits_are_bounded(search_depth, expected):
    limits = chat_sessions._retrieval_limits(search_depth)

    assert limits == expected


@pytest.mark.asyncio
async def test_mixed_retrieval_combines_knowledge_base_and_web_context(monkeypatch):
    calls = []
    paper = SimpleNamespace(title="Multimodal Research", arxiv_id="2606.00001", year=2026)

    class _FakeRAGService:
        def __init__(self, session):
            self.session = session

        async def search_similar(self, query, top_k):
            calls.append(("rag", query, top_k))
            return [(paper, 0.91234)]

        async def build_rag_context(self, query, max_papers):
            calls.append(("rag_context", query, max_papers))
            return "knowledge-base paper context"

    async def _fake_search_web_results(query, max_results, search_depth):
        calls.append(("web", query, max_results, search_depth))
        return [WebSearchResult(
            title="Web result",
            snippet="recent result",
            url="https://example.com",
            provider="bing",
            query=query,
            rank=0,
        )]

    monkeypatch.setattr(chat_sessions, "AsyncSessionLocal", lambda: _AsyncContext())
    monkeypatch.setattr(chat_sessions, "RAGService", _FakeRAGService)
    monkeypatch.setattr(chat_sessions, "search_web_results", _fake_search_web_results)

    context = []
    references = await chat_sessions._append_retrieval_context(
        context,
        "multimodal models",
        rag_enabled=True,
        web_search_enabled=True,
        search_depth="deep",
    )

    assert calls == [
        ("rag", "multimodal models", 5),
        ("rag_context", "multimodal models", 5),
        ("web", "multimodal models", 8, "deep"),
    ]
    assert "联网检索获得的网页来源" in context[0]["content"]
    assert "知识库" in context[1]["content"]
    assert references == [
        {"title": "Multimodal Research", "arxiv_id": "2606.00001", "year": 2026, "similarity": 0.9123, "source": "local_library"},
        {
            "title": "Web result",
            "url": "https://example.com",
            "source": "web",
            "provider": "bing",
            "query": "multimodal models",
            "retrieval_query": "multimodal models",
            "rank": 0,
            "snippet": "recent result",
        },
    ]


@pytest.mark.asyncio
async def test_web_search_failure_keeps_direct_chat_available(monkeypatch):
    async def _fake_search_web_results(query, max_results, search_depth):
        return []

    monkeypatch.setattr(chat_sessions, "search_web_results", _fake_search_web_results)

    context = []
    references = await chat_sessions._append_retrieval_context(
        context,
        "latest research",
        rag_enabled=False,
        web_search_enabled=True,
        search_depth="deep",
    )

    assert len(context) == 1
    assert "未返回可用来源" in context[0]["content"]
    assert references == []


def test_retrieval_status_reports_web_source_count():
    status = chat_sessions._retrieval_status(
        [
            {"source": "local_library"},
            {"source": "web"},
            {"source": "web"},
        ],
        web_search_enabled=True,
    )

    assert status == "已完成资料检索：知识库 1 篇，联网来源 2 条，正在生成回答..."


def test_retrieval_status_explicitly_reports_empty_web_results():
    status = chat_sessions._retrieval_status(
        [{"source": "local_library"}],
        web_search_enabled=True,
    )

    assert "联网增强未获取到有效网页来源" in status
