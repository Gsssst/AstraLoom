"""Regression tests for reliable local retrieval and evaluation metrics."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import papers as papers_api
from app.core.security import require_admin
from app.main import app
from app.services import hybrid_search
from app.services.hybrid_search import HybridSearchService
from app.services.retrieval_evaluation import (
    calculate_ranking_metrics,
    normalize_document_key,
)


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


def test_academic_tokenizer_normalizes_punctuation_and_case():
    tokens = hybrid_search.tokenize_academic_text("BERT attention-based top-p 模型")

    assert tokens == ["bert", "attention-based", "top-p", "模", "型"]


def test_invalidate_bm25_index_clears_cached_state():
    hybrid_search._bm25_index = {
        "corpus": [["cached"]],
        "model": object(),
        "paper_ids": [uuid4()],
        "fingerprint": (1, "old"),
    }

    hybrid_search.invalidate_bm25_index()

    assert hybrid_search._bm25_index == {
        "corpus": [],
        "model": None,
        "paper_ids": [],
        "fingerprint": None,
    }


@pytest.mark.asyncio
async def test_bm25_index_rebuilds_when_fingerprint_changes(monkeypatch):
    paper_id = uuid4()
    session = SimpleNamespace()
    service = HybridSearchService(session)
    fingerprints = iter([(1, "first"), (1, "first"), (2, "second")])
    builds = []

    async def fake_fingerprint():
        return next(fingerprints)

    class _PaperRows:
        def all(self):
            builds.append(True)
            return [(paper_id, "Transformer", "attention")]

    async def fake_execute(_statement):
        return _PaperRows()

    session.execute = fake_execute
    monkeypatch.setattr(service, "_get_index_fingerprint", fake_fingerprint)
    hybrid_search.invalidate_bm25_index()

    await service._ensure_bm25_index()
    await service._ensure_bm25_index()
    await service._ensure_bm25_index()

    assert len(builds) == 2


@pytest.mark.asyncio
async def test_search_dispatches_without_calling_unselected_modes(monkeypatch):
    service = HybridSearchService(SimpleNamespace())
    calls = []

    async def fake_bm25(query, top_k):
        calls.append(("bm25", query, top_k))
        return [("lexical", 1.0)]

    async def fail_dense(*_args, **_kwargs):
        raise AssertionError("dense retrieval must not run in bm25 mode")

    monkeypatch.setattr(service, "search_bm25", fake_bm25)
    monkeypatch.setattr(service, "search_dense", fail_dense)

    assert await service.search("LoRA", top_k=4, mode="bm25") == [("lexical", 1.0)]
    assert calls == [("bm25", "LoRA", 4)]


@pytest.mark.asyncio
async def test_weighted_rrf_promotes_overlap_and_falls_back_from_dense(monkeypatch):
    service = HybridSearchService(SimpleNamespace())

    async def fake_bm25(_query, _top_k):
        return [("lexical", 1.0), ("overlap", 0.8)]

    async def fake_dense(_query, _top_k):
        return [("overlap", 0.9), ("dense", 0.7)]

    async def full_coverage():
        return 1.0

    monkeypatch.setattr(service, "search_bm25", fake_bm25)
    monkeypatch.setattr(service, "search_dense", fake_dense)
    monkeypatch.setattr(service, "embedding_coverage", full_coverage)

    fused = await service.search_hybrid("attention", top_k=3)

    assert fused[0] == ("overlap", 1.0)

    async def unavailable_dense(_query, _top_k):
        raise RuntimeError("embedding model unavailable")

    monkeypatch.setattr(service, "search_dense", unavailable_dense)

    degraded = await service.search_hybrid("attention", top_k=3)

    assert degraded[0] == ("lexical", 1.0)
    assert [paper_id for paper_id, _score in degraded] == ["lexical", "overlap"]


@pytest.mark.asyncio
async def test_hybrid_defers_dense_fusion_for_partial_embedding_coverage(monkeypatch):
    service = HybridSearchService(SimpleNamespace())

    async def fake_bm25(_query, _top_k):
        return [("exact-lexical", 1.0)]

    async def fail_dense(_query, _top_k):
        raise AssertionError("dense retrieval must wait for sufficient coverage")

    async def partial_coverage():
        return 0.1

    monkeypatch.setattr(service, "search_bm25", fake_bm25)
    monkeypatch.setattr(service, "search_dense", fail_dense)
    monkeypatch.setattr(service, "embedding_coverage", partial_coverage)

    fused = await service.search_hybrid("attention", top_k=2)

    assert fused == [("exact-lexical", 1.0)]


@pytest.mark.asyncio
async def test_ranked_api_requests_later_page_window_and_forwards_filters(monkeypatch):
    first = SimpleNamespace(
        id=uuid4(), title="first", authors=[], year=2024, abstract="", arxiv_id=None,
        doi=None, source="manual", citation_count=0, created_at=None,
    )
    second = SimpleNamespace(
        id=uuid4(), title="second", authors=[], year=2025, abstract="", arxiv_id=None,
        doi=None, source="manual", citation_count=0, created_at=None,
    )
    captured = {}

    async def fake_search(_self, query, top_k, mode):
        captured["search"] = (query, top_k, mode)
        return [(str(first.id), 1.0), (str(second.id), 0.8)]

    async def fake_fetch(_self, scored, category=None, year_from=None, year_to=None):
        captured["filters"] = (category, year_from, year_to)
        return [(first, 1.0), (second, 0.8)]

    monkeypatch.setattr(HybridSearchService, "search", fake_search)
    monkeypatch.setattr(HybridSearchService, "fetch_papers", fake_fetch)

    result = await papers_api.search_papers(
        q="attention",
        source="local",
        category="cs.LG",
        year_from=2020,
        year_to=2026,
        page=2,
        page_size=1,
        sort="created_desc",
        search_mode="dense",
        db=SimpleNamespace(),
    )

    assert captured == {
        "search": ("attention", 100, "dense"),
        "filters": ("cs.LG", 2020, 2026),
    }
    assert [paper.title for paper in result.items] == ["second"]


@pytest.mark.asyncio
async def test_semantic_scholar_preview_uses_selected_remote_provider(monkeypatch):
    captured = []
    preview = SimpleNamespace(
        title="Remote preview", authors=[], year=2026, abstract="", arxiv_id=None,
        doi="10.1000/example", source="semantic_scholar", citation_count=2,
    )

    async def fake_search(**kwargs):
        captured.append(kwargs)
        return [preview]

    monkeypatch.setattr(papers_api.semantic_scholar_service, "search", fake_search)

    result = await papers_api.search_papers(
        q="retrieval",
        source="semantic_scholar",
        category=None,
        year_from=2020,
        year_to=2026,
        page=1,
        page_size=5,
        sort="created_desc",
        search_mode="hybrid",
        db=SimpleNamespace(),
    )

    assert captured == [{"query": "retrieval", "max_results": 5, "start": 0, "year_from": 2020, "year_to": 2026}]
    assert result.items[0].title == "Remote preview"
    assert result.items[0].id == ""


def test_ranking_metrics_report_recall_mrr_and_ndcg():
    cases = [
        {"id": "first", "query": "q1", "relevant_ids": ["arxiv:1234.5678v2"]},
        {"id": "missing", "query": "q2", "relevant_ids": ["arxiv:9999.0001"]},
    ]
    rankings = {
        "first": ["arxiv:0000.0001", "arxiv:1234.5678"],
        "missing": ["arxiv:0000.0001"],
    }

    metrics = calculate_ranking_metrics(cases, rankings, top_k=3)

    assert normalize_document_key("arxiv:1234.5678v2") == "arxiv:1234.5678"
    assert metrics["case_count"] == 2
    assert metrics["recall_at_k"] == 0.5
    assert metrics["mrr"] == 0.25
    assert metrics["ndcg_at_k"] == 0.3155


def test_search_evaluation_route_is_fixed_path_and_admin_only():
    paths = [route.path for route in app.routes]

    assert paths.index("/api/papers/search-evaluation") < paths.index("/api/papers/{paper_id}")
    assert require_admin in _dependency_calls("/api/papers/search-evaluation", "GET")
