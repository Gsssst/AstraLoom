"""Regression tests for knowledge-base retrieval maintenance utilities."""

from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException
import pytest

from app.api import papers as papers_api
from app.api.chat_sessions import _retrieval_status
from app.core.security import require_admin
from app.main import app
from app.services import document_visual_evidence, hybrid_search, paper_processing_pipeline, report_service
from app.tasks.celery_app import celery_app
from app.tasks import paper_tasks


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
        ("/api/papers/maintenance/backfill-visual-evidence", "POST"),
        ("/api/papers/maintenance/jobs/{job_id}", "GET"),
        ("/api/papers/maintenance/recommendations", "GET"),
        ("/api/papers/maintenance/search-diagnostics", "GET"),
        ("/api/papers/visual-evidence-assets/{paper_id}/{asset_token}", "GET"),
    ]:
        assert paths.index(path) < paths.index("/api/papers/{paper_id}")
        if path.startswith("/api/papers/visual-evidence-assets"):
            continue
        assert require_admin in _dependency_calls(path, method)


def test_single_paper_visual_evidence_route_is_admin_only():
    assert require_admin in _dependency_calls("/api/papers/{paper_id}/extract-visual-evidence", "POST")


def test_processing_status_route_is_fixed_path_before_paper_detail():
    paths = [route.path for route in app.routes]

    assert paths.index("/api/papers/processing-status") < paths.index("/api/papers/{paper_id}")
    assert paths.index("/api/papers/processing-automation") < paths.index("/api/papers/{paper_id}")


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
        "missing": ["full_text", "structured_parse", "visual_evidence", "embedding"],
        "failed": [],
        "status": "needs_processing",
        "labels": flags["labels"],
        "automation": flags["automation"],
    }
    assert status.status == "needs_processing"
    assert [action["key"] for action in status.repair_actions] == [
        "full_text",
        "structured_parse",
        "visual_evidence",
        "embedding",
    ]
    assert [label["key"] for label in status.processing_labels] == [
        "pdf",
        "full_text",
        "structured_parse",
        "visual_evidence",
        "embedding",
        "bm25",
    ]
    assert status.structured_parse_status.ready is False
    assert status.visual_evidence_status.ready is False


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
    assert "table_repair" not in status
    assert "table_command" not in status["parser_health"]["available"]


def test_visual_evidence_status_reports_ready_counts():
    from app.services import document_visual_evidence

    paper = SimpleNamespace(
        pdf_path="/data/paper.pdf",
        metadata_json={
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "source_path": "/data/paper.pdf",
                "parser": "docling",
                "status": "ready",
                "parsed_at": "2026-06-12T12:00:00+00:00",
                "page_count": 6,
                "items": [
                    {"id": "v1", "kind": "architecture", "page": 2, "status": "ready", "summary": "method diagram"},
                    {"id": "t1", "kind": "table", "page": 4, "status": "ready", "markdown": "| A | B |"},
                ],
            }
        },
    )

    status = document_visual_evidence.visual_evidence_status_from_paper(paper)

    assert status["ready"] is True
    assert status["item_count"] == 2
    assert status["visual_count"] == 1
    assert status["table_count"] == 1
    assert status["missing_summary_count"] == 0
    assert status["missing_ocr_count"] == 0


def test_visual_evidence_refresh_needed_includes_ready_but_incomplete_status():
    assert papers_api._visual_evidence_needs_extraction({"ready": False}) is True
    assert papers_api._visual_evidence_needs_extraction({"ready": True, "failed": True}) is True
    assert papers_api._visual_evidence_needs_extraction({"ready": True, "missing_ocr_count": 1}) is True
    assert papers_api._visual_evidence_needs_extraction({"ready": True, "missing_summary_count": 1}) is True
    assert papers_api._visual_evidence_needs_extraction({"ready": True, "low_confidence_table_count": 1}) is True
    assert papers_api._visual_evidence_needs_extraction({"ready": True, "missing_ocr_count": 0}) is False


def test_safe_paper_metadata_strips_private_visual_asset_paths():
    metadata = {
        "document_visual_evidence": {
            "items": [
                {
                    "id": "v1",
                    "asset_path": "/private/crop.png",
                    "thumbnail_path": "/private/thumb.png",
                    "asset_token": "abc",
                    "metadata": {
                        "page_asset_path": "/private/page.png",
                        "fallback_asset_path": "/private/fallback.png",
                        "page_asset_token": "page-token",
                    },
                }
            ]
        }
    }

    safe = papers_api._safe_paper_metadata(metadata)

    item = safe["document_visual_evidence"]["items"][0]
    assert "asset_path" not in item
    assert "thumbnail_path" not in item
    assert item["asset_token"] == "abc"
    assert "page_asset_path" not in item["metadata"]
    assert item["metadata"]["page_asset_token"] == "page-token"


@pytest.mark.asyncio
async def test_paper_detail_includes_visual_status_without_crashing(monkeypatch):
    paper_id = uuid4()
    paper = SimpleNamespace(
        id=paper_id,
        title="Visual detail paper",
        authors=["A"],
        year=2026,
        abstract="Abstract",
        arxiv_id="2604.17087v1",
        doi=None,
        source="arxiv",
        source_url="https://arxiv.org/abs/2604.17087v1",
        pdf_path="/data/paper.pdf",
        citation_count=0,
        imported_by_user_id=None,
        imported_by_username="gst",
        importance_label=None,
        importance_note=None,
        full_text="x" * 800,
        tags={},
        categories=[],
        metadata_json={},
        created_at=None,
    )

    class _Enhance:
        def __init__(self, _db):
            pass

        async def similar_papers(self, _paper, top_k=3):
            return []

    monkeypatch.setattr(papers_api, "PaperEnhanceService", _Enhance)

    detail = await papers_api.get_paper_detail(
        str(paper_id),
        db=_PaperDb(paper),
        user=SimpleNamespace(role="admin"),
    )

    assert detail.id == str(paper_id)
    assert detail.visual_evidence_status.status == "missing"
    assert detail.structured_parse_status.ready is False
    assert [label["key"] for label in detail.processing_labels] == [
        "pdf",
        "full_text",
        "structured_parse",
        "visual_evidence",
        "embedding",
        "bm25",
    ]


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


@pytest.mark.asyncio
async def test_visual_evidence_backfill_repairs_bounded_and_failed_candidates(monkeypatch):
    ready_paper = SimpleNamespace(
        id=uuid4(),
        title="Already visual",
        year=2026,
        arxiv_id=None,
        pdf_path="/data/ready.pdf",
        metadata_json={
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "status": "ready",
                "items": [{"id": "v-ready", "kind": "figure", "status": "ready", "summary": "ready"}],
            }
        },
    )
    missing_paper = SimpleNamespace(id=uuid4(), title="Needs visual", year=2026, arxiv_id=None, pdf_path="/data/missing.pdf", metadata_json={})
    failed_paper = SimpleNamespace(
        id=uuid4(),
        title="Retry failed visual",
        year=2026,
        arxiv_id=None,
        pdf_path="/data/failed.pdf",
        metadata_json={
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "status": "failed",
                "last_error": {"message": "old failure"},
                "items": [],
            }
        },
    )

    class _Db:
        commits = 0

        async def execute(self, _statement):
            return _ScalarListResult([ready_paper, missing_paper, failed_paper])

        async def commit(self):
            self.commits += 1

    async def fake_ensure(paper, _db, force=False):
        assert force is True
        paper.metadata_json = {
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "status": "ready",
                "items": [{"id": f"v-{paper.id}", "kind": "figure", "status": "ready", "summary": "visual"}],
            }
        }
        return paper.metadata_json[document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY]

    monkeypatch.setattr(document_visual_evidence, "ensure_document_visual_evidence", fake_ensure)

    db = _Db()
    result = await papers_api._run_visual_evidence_backfill(db, limit=2)

    assert result.processed == 2
    assert result.success == 2
    assert result.failed == 0
    assert db.commits == 1


@pytest.mark.asyncio
async def test_visual_evidence_backfill_repairs_ready_items_missing_ocr(monkeypatch):
    incomplete_paper = SimpleNamespace(
        id=uuid4(),
        title="Ready but missing OCR",
        year=2026,
        arxiv_id=None,
        pdf_path="/data/incomplete.pdf",
        metadata_json={
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "status": "ready",
                "items": [{"id": "t1", "kind": "table", "status": "ready", "summary": "table"}],
            }
        },
    )

    class _Db:
        commits = 0

        async def execute(self, _statement):
            return _ScalarListResult([incomplete_paper])

        async def commit(self):
            self.commits += 1

    async def fake_ensure(paper, _db, force=False):
        assert paper is incomplete_paper
        assert force is True
        paper.metadata_json = {
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "status": "ready",
                "items": [{"id": "t1", "kind": "table", "status": "ready", "markdown": "| A | B |"}],
            }
        }
        return paper.metadata_json[document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY]

    monkeypatch.setattr(document_visual_evidence, "ensure_document_visual_evidence", fake_ensure)

    db = _Db()
    result = await papers_api._run_visual_evidence_backfill(db, limit=1)

    assert result.processed == 1
    assert result.success == 1
    assert db.commits == 1


@pytest.mark.asyncio
async def test_visual_evidence_backfill_enqueue_returns_pollable_job(monkeypatch):
    created = []

    class _Task:
        def __init__(self, coro):
            self.coro = coro

    def fake_create_task(coro):
        created.append(coro)
        return _Task(coro)

    monkeypatch.setattr(papers_api.asyncio, "create_task", fake_create_task)

    response = await papers_api.backfill_visual_evidence(limit=3, user=SimpleNamespace(role="admin"))

    assert response.job_id.startswith("visual-evidence-")
    assert response.job.kind == "visual_evidence_backfill"
    assert response.job.state == "queued"
    assert response.job.total == 3
    assert papers_api._MAINTENANCE_JOBS[response.job_id].id == response.job_id
    assert created
    created[0].close()


@pytest.mark.asyncio
async def test_maintenance_job_status_reads_local_visual_job_before_celery():
    job = papers_api.MaintenanceJobStatus(
        id="visual-evidence-test",
        kind="visual_evidence_backfill",
        state="running",
        status="running",
        total=2,
        processed=1,
        progress_percent=50,
    )
    papers_api._MAINTENANCE_JOBS[job.id] = job
    try:
        status = await papers_api.get_maintenance_job_status(job.id, user=SimpleNamespace(role="admin"))
    finally:
        papers_api._MAINTENANCE_JOBS.pop(job.id, None)

    assert status.kind == "visual_evidence_backfill"
    assert status.state == "running"
    assert status.progress_percent == 50


@pytest.mark.asyncio
async def test_single_paper_visual_evidence_enqueue_returns_pollable_job(monkeypatch):
    paper_id = uuid4()
    paper = SimpleNamespace(id=paper_id, title="Needs visual OCR", year=2026, metadata_json={})

    class _Db:
        async def execute(self, _statement):
            return _ScalarOneResult(paper)

    created = []

    class _Task:
        def __init__(self, coro):
            self.coro = coro

    def fake_create_task(coro):
        created.append(coro)
        return _Task(coro)

    async def fail_sync_reparse(*_args, **_kwargs):
        raise AssertionError("single-paper endpoint should enqueue instead of synchronously reparsing")

    monkeypatch.setattr(papers_api.asyncio, "create_task", fake_create_task)
    monkeypatch.setattr(document_visual_evidence, "ensure_document_visual_evidence", fail_sync_reparse)

    response = await papers_api.extract_paper_visual_evidence(
        str(paper_id),
        db=_Db(),
        user=SimpleNamespace(role="admin"),
    )

    try:
        assert response.job_id
        assert response.job is not None
        assert response.job.kind == "visual_evidence_single_paper"
        assert response.job.state == "queued"
        assert response.status == "missing"
        assert papers_api._MAINTENANCE_JOBS[response.job_id].id == response.job_id
        assert papers_api._SINGLE_VISUAL_EVIDENCE_JOBS_BY_PAPER[str(paper_id)] == response.job_id
        assert created
    finally:
        for coro in created:
            coro.close()
        papers_api._MAINTENANCE_JOBS.pop(response.job_id or "", None)
        papers_api._SINGLE_VISUAL_EVIDENCE_JOBS_BY_PAPER.pop(str(paper_id), None)


@pytest.mark.asyncio
async def test_single_paper_visual_evidence_enqueue_deduplicates_running_job(monkeypatch):
    paper_id = uuid4()
    paper = SimpleNamespace(id=paper_id, title="Needs visual OCR", year=2026, metadata_json={})
    existing = papers_api.MaintenanceJobStatus(
        id="visual-evidence-paper-existing",
        kind="visual_evidence_single_paper",
        state="running",
        status="running",
        total=1,
        current_paper={"id": str(paper_id), "title": paper.title},
    )
    papers_api._MAINTENANCE_JOBS[existing.id] = existing
    papers_api._SINGLE_VISUAL_EVIDENCE_JOBS_BY_PAPER[str(paper_id)] = existing.id

    class _Db:
        async def execute(self, _statement):
            return _ScalarOneResult(paper)

    def fail_create_task(_coro):
        raise AssertionError("duplicate click should reuse active single-paper job")

    monkeypatch.setattr(papers_api.asyncio, "create_task", fail_create_task)

    try:
        response = await papers_api.extract_paper_visual_evidence(
            str(paper_id),
            db=_Db(),
            user=SimpleNamespace(role="admin"),
        )
    finally:
        papers_api._MAINTENANCE_JOBS.pop(existing.id, None)
        papers_api._SINGLE_VISUAL_EVIDENCE_JOBS_BY_PAPER.pop(str(paper_id), None)

    assert response.job_id == existing.id
    assert response.job is not None
    assert response.job.state == "running"


def test_maintenance_job_status_normalizes_progress_payload():
    payload = {
        "kind": "maintenance",
        "status": "running",
        "total": 5,
        "processed": 2,
        "success": 1,
        "failed": 0,
        "skipped": 1,
        "progress_percent": 40,
        "current_paper": {"id": "paper-1", "title": "Current paper"},
        "message": "正在维护",
    }
    async_result = SimpleNamespace(state="PROGRESS", info=payload, result=None)

    status = papers_api._maintenance_job_status_from_result("job-1", async_result)

    assert status.id == "job-1"
    assert status.state == "running"
    assert status.total == 5
    assert status.processed == 2
    assert status.progress_percent == 40
    assert status.current_paper["title"] == "Current paper"


def test_maintenance_job_status_normalizes_success_result():
    async_result = SimpleNamespace(
        state="SUCCESS",
        info=None,
        result={
            "kind": "maintenance",
            "status": "success",
            "processed": 3,
            "success": 2,
            "failed": 1,
            "skipped": 0,
            "result": {"processed": 3, "success": 2, "failed": 1, "skipped": 0, "errors": [{"reason": "bad"}]},
        },
    )

    status = papers_api._maintenance_job_status_from_result("job-2", async_result)

    assert status.state == "success"
    assert status.progress_percent == 100
    assert status.result.success == 2
    assert status.result.errors[0]["reason"] == "bad"


def test_processing_flags_require_pdf_artifacts_when_pdf_is_available():
    paper = SimpleNamespace(
        metadata_json={},
        pdf_path="/data/paper.pdf",
        full_text="x" * 600,
        embedding=[0.1, 0.2],
        tags={"methods": ["retrieval"]},
    )

    flags = papers_api._paper_processing_flags(paper)

    assert flags["status"] == "needs_processing"
    assert "structured_parse" in flags["missing"]
    assert "visual_evidence" in flags["missing"]


def test_processing_flags_mark_ready_when_all_automatic_artifacts_exist():
    hybrid_search._bm25_index = {
        "corpus": [["ready"]],
        "model": object(),
        "paper_ids": [uuid4()],
        "fingerprint": (1, "2026-06-13T00:00:00"),
    }
    paper = SimpleNamespace(
        metadata_json={
            report_service.PDF_STRUCTURED_METADATA_KEY: {
                "version": report_service.PDF_STRUCTURED_METADATA_VERSION,
                "source_path": "/data/paper.pdf",
                "parser": "test",
                "page_count": 1,
                "blocks": [{"type": "text", "text": "content"}],
            },
            document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_KEY: {
                "version": document_visual_evidence.DOCUMENT_VISUAL_EVIDENCE_VERSION,
                "source_path": "/data/paper.pdf",
                "status": "ready",
                "items": [{"id": "v1", "kind": "figure", "status": "ready", "summary": "figure"}],
            },
        },
        pdf_path="/data/paper.pdf",
        full_text="x" * 600,
        embedding=[0.1, 0.2],
        tags=[],
    )

    assert papers_api._paper_processing_flags(paper)["status"] == "ready"


def test_processing_snapshot_does_not_require_tags_or_manual_pdf_for_ready_status():
    paper = SimpleNamespace(
        metadata_json={},
        pdf_path=None,
        arxiv_id=None,
        full_text="x" * 600,
        embedding=[0.1, 0.2],
        tags=[],
    )

    snapshot = paper_processing_pipeline.paper_processing_snapshot(
        paper,
        bm25_status={"ready": True, "indexed_papers": 1},
    )

    assert snapshot.status == "ready"
    assert snapshot.missing == []
    labels = {label.key: label for label in snapshot.labels}
    assert labels["structured_parse"].state == "pending"
    assert labels["visual_evidence"].state == "pending"


def test_celery_registers_paper_processing_pipeline_schedule():
    assert "app.tasks.paper_tasks" in celery_app.conf.include
    celery_app.loader.import_default_modules()

    assert "process_paper_pipeline" in celery_app.tasks
    assert "reconcile_paper_processing" in celery_app.tasks
    schedule = celery_app.conf.beat_schedule["reconcile-paper-processing"]
    assert schedule["task"] == "reconcile_paper_processing"
    assert schedule["kwargs"]["limit"] == 5


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


def test_reconcile_task_skips_when_singleton_lock_is_held(monkeypatch):
    class _HeldLock:
        acquired = False

        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(paper_tasks, "_RedisTaskLock", _HeldLock)

    result = paper_tasks.reconcile_paper_processing.run(limit=5)

    assert result["status"] == "skipped"
    assert result["locked"] is True
    assert result["processed"] == 0
    assert result["message"] == "paper processing reconciliation already running"


def test_reconcile_task_releases_singleton_lock(monkeypatch):
    events = []

    class _OwnedLock:
        acquired = True

        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            events.append("enter")
            return self

        def __exit__(self, *_args):
            events.append("exit")
            return False

    async def fake_reconcile(self, **_kwargs):
        return {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "items": [],
            "errors": [],
        }

    monkeypatch.setattr(paper_tasks, "_RedisTaskLock", _OwnedLock)
    monkeypatch.setattr(paper_processing_pipeline.PaperProcessingPipeline, "reconcile_batch", fake_reconcile)

    result = paper_tasks.reconcile_paper_processing.run(limit=5)

    assert result["status"] == "success"
    assert events == ["enter", "exit"]


def test_processing_running_state_classifies_fresh_and_stale():
    fresh = SimpleNamespace(
        metadata_json={
            paper_processing_pipeline.PIPELINE_METADATA_KEY: {
                "running_steps": ["visual_evidence"],
                "last_checked_at": "2026-06-13T00:00:00+00:00",
            }
        }
    )
    stale = SimpleNamespace(
        metadata_json={
            paper_processing_pipeline.PIPELINE_METADATA_KEY: {
                "running_steps": ["visual_evidence"],
                "last_checked_at": "2026-06-12T20:00:00+00:00",
            }
        }
    )
    now = paper_processing_pipeline.datetime.fromisoformat("2026-06-13T00:30:00+00:00")

    assert paper_processing_pipeline.paper_processing_running_state(fresh, now=now, ttl_seconds=7200)["fresh"] is True
    assert paper_processing_pipeline.paper_processing_running_state(stale, now=now, ttl_seconds=7200)["stale"] is True


@pytest.mark.asyncio
async def test_reconcile_batch_skips_fresh_running_and_retries_stale(monkeypatch):
    fresh = SimpleNamespace(
        id=uuid4(),
        title="Fresh running",
        arxiv_id="2606.00001",
        pdf_path=None,
        full_text=None,
        embedding=None,
        tags=[],
        metadata_json={
            paper_processing_pipeline.PIPELINE_METADATA_KEY: {
                "running_steps": ["visual_evidence"],
                "last_checked_at": "2026-06-13T00:00:00+00:00",
            },
            "pdf_url": "https://arxiv.org/pdf/2606.00001",
        },
    )
    stale = SimpleNamespace(
        id=uuid4(),
        title="Stale running",
        arxiv_id="2606.00002",
        pdf_path=None,
        full_text=None,
        embedding=None,
        tags=[],
        metadata_json={
            paper_processing_pipeline.PIPELINE_METADATA_KEY: {
                "running_steps": ["visual_evidence"],
                "last_checked_at": "2026-06-12T20:00:00+00:00",
            },
            "pdf_url": "https://arxiv.org/pdf/2606.00002",
        },
    )

    class _Rows:
        def all(self):
            return [fresh, stale]

    class _Result:
        def scalars(self):
            return _Rows()

    class _Session:
        async def execute(self, _statement):
            return _Result()

        async def commit(self):
            return None

        async def refresh(self, _paper):
            return None

    async def fake_process(self, paper_id, **_kwargs):
        return paper_processing_pipeline.PaperProcessingResult(
            paper_id=str(paper_id),
            title="Stale running",
            completed=["full_text"],
        )

    fixed_now = paper_processing_pipeline.datetime.fromisoformat("2026-06-13T00:30:00+00:00")

    class _FixedDateTime(paper_processing_pipeline.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(paper_processing_pipeline, "datetime", _FixedDateTime)
    monkeypatch.setattr(paper_processing_pipeline.PaperProcessingPipeline, "process_paper", fake_process)

    summary = await paper_processing_pipeline.PaperProcessingPipeline(_Session()).reconcile_batch(
        limit=5,
        running_ttl_seconds=7200,
        rebuild_bm25=False,
    )

    assert summary["processed"] == 1
    assert summary["success"] == 1
    assert summary["skipped_running"] == 1
    assert summary["stale_running_cleared"] == 1
    assert fresh.metadata_json[paper_processing_pipeline.PIPELINE_METADATA_KEY]["running_steps"] == ["visual_evidence"]
    assert stale.metadata_json[paper_processing_pipeline.PIPELINE_METADATA_KEY]["running_steps"] == []
