"""Regression tests for knowledge-base retrieval maintenance utilities."""

from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException
import pytest

from app.api import papers as papers_api
from app.api.chat_sessions import _retrieval_status
from app.core.security import require_admin
from app.main import app
from app.services import hybrid_search, report_service


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
        ("/api/papers/maintenance/backfill-structured-pdf", "POST"),
        ("/api/papers/maintenance/recommendations", "GET"),
        ("/api/papers/maintenance/search-diagnostics", "GET"),
    ]:
        assert paths.index(path) < paths.index("/api/papers/{paper_id}")
        assert require_admin in _dependency_calls(path, method)


def test_processing_status_route_is_fixed_path_before_paper_detail():
    paths = [route.path for route in app.routes]

    assert paths.index("/api/papers/processing-status") < paths.index("/api/papers/{paper_id}")


def test_processing_flags_and_repair_actions_reflect_missing_artifacts():
    paper = SimpleNamespace(
        id=uuid4(),
        title="Partial paper",
        year=2026,
        source="arxiv",
        arxiv_id="2606.00001",
        imported_by_username="gst",
        metadata_json={"pdf_url": "https://arxiv.org/pdf/2606.00001"},
        pdf_path=None,
        full_text="too short",
        embedding=None,
        tags=[],
    )

    flags = papers_api._paper_processing_flags(paper)
    status = papers_api._paper_processing_status(paper)

    assert flags == {
        "has_pdf": True,
        "has_full_text": False,
        "has_embedding": False,
        "has_tags": False,
        "missing": ["full_text", "embedding", "tags"],
        "status": "needs_processing",
    }
    assert status.status == "needs_processing"
    assert [action["key"] for action in status.repair_actions] == ["full_text", "structured_parse", "embedding", "tags"]
    assert status.structured_parse_status.ready is False


def test_structured_parse_status_reports_cached_counts_and_parser():
    paper = SimpleNamespace(
        pdf_path="/data/paper.pdf",
        metadata_json={
            report_service.PDF_STRUCTURED_METADATA_KEY: {
                "version": report_service.PDF_STRUCTURED_METADATA_VERSION,
                "source_path": "/data/paper.pdf",
                "parser": "docling",
                "parsed_at": "2026-06-11T12:00:00+00:00",
                "page_count": 9,
                "table_count": 2,
                "caption_count": 3,
                "visual_count": 1,
                "blocks": [
                    {"type": "table", "text": "table", "page": 4},
                    {"type": "ocr", "text": "ocr", "page": 5},
                    {"type": "formula", "text": "formula", "page": 6},
                ],
            }
        },
    )

    status = report_service.structured_pdf_parse_status_from_paper(paper)

    assert status["ready"] is True
    assert status["parser"] == "docling"
    assert status["page_count"] == 9
    assert status["table_count"] == 2
    assert status["ocr_count"] == 1
    assert status["formula_count"] == 1
    assert status["block_count"] == 3
    assert status["table_quality"]["table_count"] == 1
    assert status["table_quality"]["quality"] in {"high", "medium", "low"}
    assert status["parser_health"]["configured_backend"]


def test_parser_runtime_health_reports_available_backends(monkeypatch):
    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_BACKEND", "auto")
    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_COMMAND", "")
    monkeypatch.setattr(report_service.settings, "HF_ENDPOINT", "https://hf-mirror.com")

    health = report_service.parser_runtime_health()

    assert health["configured_backend"] == "auto"
    assert "pdfplumber" in health["available"]
    assert health["available"]["command"] is False
    assert health["hf_endpoint"] == "https://hf-mirror.com"


class _ScalarOneResult:
    def __init__(self, item):
        self.item = item

    def scalar_one_or_none(self):
        return self.item


class _ScalarListResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


class _PaperDb:
    def __init__(self, paper):
        self.paper = paper
        self.commits = 0
        self.refreshed = []
        self.executed = []

    async def execute(self, statement):
        self.executed.append(statement)
        return _ScalarOneResult(self.paper)

    async def commit(self):
        self.commits += 1

    async def refresh(self, paper):
        self.refreshed.append(paper)


@pytest.mark.asyncio
async def test_reparse_structured_pdf_endpoint_refreshes_metadata(monkeypatch):
    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Structured paper",
        arxiv_id=None,
        pdf_path="/data/paper.pdf",
        metadata_json={
            report_service.PDF_STRUCTURED_PARSE_ERROR_KEY: {"message": "old failure"}
        },
    )
    db = _PaperDb(paper)

    def fake_extract(path):
        assert path == "/data/paper.pdf"
        return report_service.StructuredPdfExtraction(
            source_path=path,
            page_count=4,
            parser="test-parser",
            blocks=[
                report_service.StructuredPdfBlock(
                    block_type="table",
                    page=2,
                    source="test",
                    text="| Model | Accuracy |",
                )
            ],
        )

    monkeypatch.setattr(report_service, "extract_pdf_structured_content", fake_extract)

    status = await papers_api.reparse_structured_pdf(str(paper_id), db=db, user=SimpleNamespace(role="admin"))

    assert status.ready is True
    assert status.parser == "test-parser"
    assert status.page_count == 4
    assert status.table_count == 1
    assert status.last_error is None
    assert report_service.PDF_STRUCTURED_PARSE_ERROR_KEY not in paper.metadata_json
    assert db.commits == 1
    assert db.refreshed == [paper]


@pytest.mark.asyncio
async def test_reparse_structured_pdf_recovers_missing_arxiv_pdf_path(monkeypatch):
    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Twilight",
        arxiv_id="2502.02770v5",
        pdf_path=None,
        full_text="x" * 50000,
        metadata_json={},
    )
    db = _PaperDb(paper)

    async def fake_cached_pdf(_arxiv_id):
        return SimpleNamespace(path="/cache/2502.02770.pdf")

    def fake_extract(path):
        assert path == "/cache/2502.02770.pdf"
        return report_service.StructuredPdfExtraction(
            source_path=path,
            page_count=12,
            parser="test-parser",
            blocks=[report_service.StructuredPdfBlock(block_type="table", text="| A | B |", page=2)],
        )

    monkeypatch.setattr(report_service, "ensure_cached_arxiv_pdf", fake_cached_pdf)
    monkeypatch.setattr(report_service, "extract_pdf_structured_content", fake_extract)

    status = await papers_api.reparse_structured_pdf(str(paper_id), db=db, user=SimpleNamespace(role="admin"))

    assert paper.pdf_path == "/cache/2502.02770.pdf"
    assert status.ready is True
    assert status.source_path == "/cache/2502.02770.pdf"


@pytest.mark.asyncio
async def test_reparse_structured_pdf_endpoint_persists_visible_failure(monkeypatch):
    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Broken paper",
        arxiv_id=None,
        pdf_path="/data/broken.pdf",
        metadata_json={},
    )
    db = _PaperDb(paper)

    def fake_extract(_path):
        raise RuntimeError("parser binary missing")

    monkeypatch.setattr(report_service, "extract_pdf_structured_content", fake_extract)
    monkeypatch.setattr(report_service.settings, "PDF_STRUCTURED_PARSER_BACKEND", "command")

    with pytest.raises(HTTPException) as raised:
        await papers_api.reparse_structured_pdf(str(paper_id), db=db, user=SimpleNamespace(role="admin"))

    assert raised.value.status_code == 500
    assert db.commits == 1
    error = paper.metadata_json[report_service.PDF_STRUCTURED_PARSE_ERROR_KEY]
    assert error["message"] == "parser binary missing"
    assert error["parser_backend"] == "command"
    assert raised.value.detail["status"]["last_error"]["message"] == "parser binary missing"


@pytest.mark.asyncio
async def test_backfill_structured_pdf_parse_repairs_bounded_candidates(monkeypatch):
    papers = [
        SimpleNamespace(id=uuid4(), title="Needs parse", arxiv_id=None, pdf_path="/data/a.pdf", metadata_json={}),
        SimpleNamespace(
            id=uuid4(),
            title="Already parsed",
            arxiv_id=None,
            pdf_path="/data/b.pdf",
            metadata_json={
                report_service.PDF_STRUCTURED_METADATA_KEY: {
                    "version": report_service.PDF_STRUCTURED_METADATA_VERSION,
                    "source_path": "/data/b.pdf",
                    "parser": "test",
                    "page_count": 1,
                    "blocks": [],
                }
            },
        ),
    ]

    class _Db:
        commits = 0

        async def execute(self, _statement):
            return _ScalarListResult(papers)

        async def commit(self):
            self.commits += 1

    async def fake_reparse(paper, db):
        paper.metadata_json = {
            report_service.PDF_STRUCTURED_METADATA_KEY: {
                "version": report_service.PDF_STRUCTURED_METADATA_VERSION,
                "source_path": paper.pdf_path,
                "parser": "test-parser",
                "page_count": 2,
                "blocks": [{"type": "table", "text": "table"}],
            }
        }
        return {"ready": True}

    monkeypatch.setattr(report_service, "force_structured_pdf_reparse", fake_reparse)

    db = _Db()
    result = await papers_api.backfill_structured_pdf_parse(limit=5, db=db, user=SimpleNamespace(role="admin"))

    assert result.processed == 1
    assert result.success == 1
    assert result.failed == 0
    assert db.commits == 1


def test_processing_flags_mark_ready_when_full_text_embedding_and_tags_exist():
    paper = SimpleNamespace(
        metadata_json={},
        pdf_path="/data/paper.pdf",
        full_text="x" * 600,
        embedding=[0.1, 0.2],
        tags={"methods": ["retrieval"]},
    )

    assert papers_api._paper_processing_flags(paper)["status"] == "ready"


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
