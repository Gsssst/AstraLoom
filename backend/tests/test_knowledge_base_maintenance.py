"""Regression tests for knowledge-base retrieval maintenance utilities."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api import papers as papers_api
from app.api.chat_sessions import _retrieval_status
from app.core.security import require_admin
from app.main import app
from app.services import hybrid_search


def _route(path: str, method: str):
    return next(
        route
        for route in app.routes
        if route.path == path and method in (route.methods or set())
    )


def _dependency_calls(path: str, method: str):
    return {dependency.call for dependency in _route(path, method).dependant.dependencies}


def test_bm25_index_status_reports_process_local_state():
    paper_id = uuid4()
    hybrid_search._bm25_index = {
        "corpus": [["attention"]],
        "model": object(),
        "paper_ids": [paper_id],
        "fingerprint": (1, "2026-06-04T00:00:00"),
    }

    status = hybrid_search.bm25_index_status()

    assert status == {
        "ready": True,
        "indexed_papers": 1,
        "corpus_documents": 1,
        "fingerprint": [1, "2026-06-04T00:00:00"],
    }


def test_maintenance_routes_are_fixed_paths_and_admin_only():
    paths = [route.path for route in app.routes]

    for path, method in [
        ("/api/papers/maintenance/health", "GET"),
        ("/api/papers/maintenance/rebuild-bm25", "POST"),
        ("/api/papers/maintenance/backfill-embeddings", "POST"),
        ("/api/papers/maintenance/backfill-full-text", "POST"),
        ("/api/papers/maintenance/recommendations", "GET"),
        ("/api/papers/maintenance/search-diagnostics", "GET"),
    ]:
        assert paths.index(path) < paths.index("/api/papers/{paper_id}")
        assert require_admin in _dependency_calls(path, method)


def test_query_match_sources_reports_matching_fields():
    paper = SimpleNamespace(
        title="Video Grounding with Temporal Localization",
        abstract="A benchmark for long video grounding.",
        full_text="The introduction discusses temporal sentence grounding in detail.",
    )

    assert papers_api._query_match_sources("temporal grounding", paper) == [
        "title",
        "abstract",
        "full_text",
    ]


@pytest.mark.asyncio
async def test_format_diagnostic_hits_preserves_score_order_and_flags():
    first_id = uuid4()
    second_id = uuid4()
    first = SimpleNamespace(
        id=first_id,
        title="First paper",
        year=2026,
        source="arxiv",
        arxiv_id="2601.00001",
        abstract="video grounding",
        full_text="x" * 600,
        embedding=[0.1],
    )
    second = SimpleNamespace(
        id=second_id,
        title="Second paper",
        year=2025,
        source="manual",
        arxiv_id=None,
        abstract="",
        full_text=None,
        embedding=None,
    )

    class _ScalarRows:
        def all(self):
            return [second, first]

    class _Result:
        def scalars(self):
            return _ScalarRows()

    async def fake_execute(_statement):
        return _Result()

    db = SimpleNamespace(execute=fake_execute)

    hits = await papers_api._format_diagnostic_hits(
        db,
        "video grounding",
        [(str(first_id), 0.9), (str(second_id), 0.4)],
    )

    assert [hit.id for hit in hits] == [str(first_id), str(second_id)]
    assert hits[0].has_full_text is True
    assert hits[0].has_embedding is True
    assert hits[0].match_sources == ["abstract"]
    assert hits[1].has_full_text is False
    assert hits[1].has_embedding is False


def test_diagnostic_explanations_report_low_embedding_coverage_and_no_hits():
    explanations = papers_api._diagnostic_branch_explanations(
        query_terms=["video", "grounding"],
        bm25_hits=[],
        dense_hits=[],
        hybrid_hits=[],
        bm25_status={"ready": True, "indexed_papers": 3},
        embedding_coverage=0.25,
        errors={},
    )

    assert "标题和摘要中没有明显词面重叠" in explanations["bm25"][0]
    assert "向量覆盖率只有 25%" in explanations["dense"][0]
    assert "Hybrid 没有可用候选" in explanations["hybrid"][0]


def test_diagnostic_summary_flags_missing_artifacts():
    hit = papers_api.RetrievalDiagnosticHit(
        id=str(uuid4()),
        title="Partial paper",
        score=0.8,
        has_full_text=False,
        has_embedding=False,
    )

    summary = papers_api._diagnostic_summary([hit], {})

    assert "Hybrid 找到 1 个候选" in summary
    assert "缺全文" in summary
    assert "缺向量" in summary


def test_retrieval_status_discloses_low_coverage_and_no_local_hits():
    status = _retrieval_status(
        [],
        web_search_enabled=False,
        retrieval_quality={"rag_enabled": True, "paper_count": 10, "embedding_coverage": 0.2},
    )

    assert "知识库本轮未命中可引用资料" in status
    assert "向量覆盖率约 20%" in status
    assert "知识库维护补索引" in status
