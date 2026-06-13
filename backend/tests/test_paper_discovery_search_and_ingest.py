"""Tests for resilient scholarly discovery and personal one-click ingestion."""

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.api import papers as papers_api
from app.services import paper_processing_pipeline
from app.services import paper_library_state
from app.services.paper_ingestion import PaperIngestionService
from app.tasks import paper_tasks
from app.services.paper_search import (
    PaperResult,
    create_remote_ingest_token,
    deduplicate_papers,
    read_remote_ingest_token,
    search_scholarly_papers,
)


def _paper(source="openalex", remote_id="W123", **overrides):
    fields = {
        "title": "Video Grounding with Evidence",
        "authors": ["Researcher"],
        "abstract": "Grounding moments in long videos.",
        "year": 2026,
        "doi": "10.1000/video-grounding",
        "source": source,
        "metadata": {"remote_id": remote_id},
    }
    fields.update(overrides)
    return PaperResult(**fields)


class _EmptyRows:
    def all(self):
        return []


class _EmptyResult:
    def scalars(self):
        return _EmptyRows()


class _EmptyDb:
    async def execute(self, _statement):
        return _EmptyResult()


def test_scholarly_deduplication_collapses_same_doi():
    papers = [
        _paper(source="openalex", remote_id="W123"),
        _paper(source="semantic_scholar", remote_id="s2-123"),
    ]

    assert deduplicate_papers(papers) == [papers[0]]


@pytest.mark.asyncio
async def test_strict_arxiv_discovery_does_not_silently_return_other_providers(monkeypatch):
    openalex_called = False

    async def fail_arxiv(*_args, **_kwargs):
        raise httpx.ReadTimeout("slow arxiv")

    async def openalex(*_args, **_kwargs):
        nonlocal openalex_called
        openalex_called = True
        return []

    monkeypatch.setattr("app.services.paper_search.arxiv_service.search", fail_arxiv)
    monkeypatch.setattr("app.services.paper_search.openalex_service.search", openalex)

    result = await search_scholarly_papers("video grounding", source="arxiv", max_results=5)

    assert result == []
    assert openalex_called is False


def test_remote_ingest_token_round_trip_rejects_tampering():
    paper = _paper()
    token = create_remote_ingest_token(paper)

    decoded = read_remote_ingest_token(token)

    assert decoded is not None
    assert decoded.title == paper.title
    assert decoded.metadata["remote_id"] == "W123"
    assert read_remote_ingest_token(token + "tampered") is None


@pytest.mark.asyncio
async def test_personal_ingestion_uses_signed_preview_and_saves_for_current_user(monkeypatch):
    preview = _paper()
    stored = SimpleNamespace(id=uuid4())
    calls = []

    async def fake_ingest(_self, paper, auto_download, imported_by_user=None):
        calls.append(("ingest", paper.metadata["remote_id"], auto_download, imported_by_user.id))
        return stored, True

    async def fake_save(_self, user_id, paper_id):
        calls.append(("save", user_id, paper_id))

    monkeypatch.setattr(papers_api.PaperIngestionService, "ingest_paper", fake_ingest)
    monkeypatch.setattr(papers_api.PaperEnhanceService, "save_paper", fake_save)
    user = SimpleNamespace(id=uuid4(), username="gst")

    response = await papers_api.ingest_personal_paper(
        papers_api.PersonalIngestRequest(
            source="openalex",
            remote_id="W123",
            remote_ingest_token=create_remote_ingest_token(preview),
        ),
        db=SimpleNamespace(),
        user=user,
    )

    assert response.success == 1
    assert response.paper_ids == [str(stored.id)]
    assert calls == [
        ("ingest", "W123", False, user.id),
        ("save", str(user.id), str(stored.id)),
    ]


def test_personal_ingestion_route_is_fixed_path_before_paper_detail():
    paths = [route.path for route in papers_api.router.routes]

    assert paths.index("/papers/ingest-personal") < paths.index("/papers/{paper_id}")


def test_remote_paper_brief_preserves_full_abstract_for_detail_modal():
    full_abstract = "complete abstract " * 80

    brief = papers_api._paper_brief(_paper(abstract=full_abstract), remote=True)

    assert len(brief.abstract) == 500
    assert brief.abstract_full == full_abstract


def test_remote_paper_brief_exposes_existing_library_state():
    local_id = str(uuid4())

    brief = papers_api._paper_brief(
        _paper(),
        remote=True,
        library_state={
            "in_library": True,
            "local_paper_id": local_id,
            "local_match_key": "doi:10.1000/video-grounding",
        },
    )

    assert brief.in_library is True
    assert brief.local_paper_id == local_id
    assert brief.local_match_key == "doi:10.1000/video-grounding"


@pytest.mark.asyncio
async def test_remote_preview_existing_state_matches_local_title():
    local = SimpleNamespace(
        id=uuid4(),
        title="Video Grounding with Evidence",
        arxiv_id=None,
        doi=None,
        source="openalex",
        metadata_json={},
    )

    class _Rows:
        def all(self):
            return [local]

    class _Result:
        def scalars(self):
            return _Rows()

    class _Db:
        async def execute(self, _statement):
            return _Result()

    lookup = await paper_library_state.local_paper_lookup_for_remote_previews(
        _Db(),
        [_paper(title="Video Grounding with Evidence", doi=None, arxiv_id=None, metadata={"remote_id": "W999"})],
    )
    state = paper_library_state.existing_state_for_preview(
        _paper(title="Video Grounding with Evidence", doi=None, arxiv_id=None, metadata={"remote_id": "W999"}),
        lookup,
    )

    assert state["in_library"] is True
    assert state["local_paper_id"] == str(local.id)
    assert state["local_match_key"] == "title:videogroundingwithevidence"


def test_local_paper_brief_exposes_importer_metadata():
    user_id = uuid4()
    paper = SimpleNamespace(
        id=uuid4(),
        title="Imported paper",
        authors=["Alice"],
        year=2026,
        abstract="A",
        arxiv_id=None,
        doi=None,
        source="manual",
        citation_count=0,
        created_at=SimpleNamespace(isoformat=lambda: "2026-06-08T00:00:00"),
        metadata_json={},
        source_url=None,
        imported_by_user_id=user_id,
        imported_by_username="gst",
        importance_label="important",
        importance_note="Shared reason",
    )

    brief = papers_api._paper_brief(paper, bm25_status={"ready": True, "indexed_papers": 1})

    assert brief.imported_by_user_id == str(user_id)
    assert brief.imported_by_username == "gst"
    assert brief.importance_label == "important"
    assert brief.importance_note == "Shared reason"


def test_local_paper_brief_exposes_processing_readiness():
    paper = SimpleNamespace(
        id=uuid4(),
        title="Ready paper",
        authors=[],
        year=2026,
        abstract="A",
        arxiv_id=None,
        doi=None,
        source="manual",
        citation_count=0,
        created_at=SimpleNamespace(isoformat=lambda: "2026-06-08T00:00:00"),
        metadata_json={"pdf_url": "https://example.test/paper.pdf"},
        source_url=None,
        imported_by_user_id=None,
        imported_by_username="gst",
        pdf_path=None,
        full_text="x" * 600,
        embedding=[0.1],
        tags=["retrieval"],
    )

    brief = papers_api._paper_brief(paper, bm25_status={"ready": True, "indexed_papers": 1})

    assert brief.has_pdf is True
    assert brief.has_full_text is True
    assert brief.has_embedding is True
    assert brief.has_tags is True
    assert brief.processing_status == "ready"
    assert [label["key"] for label in brief.processing_labels] == [
        "pdf",
        "full_text",
        "structured_parse",
        "visual_evidence",
        "embedding",
        "bm25",
    ]


@pytest.mark.asyncio
async def test_ingest_paper_enqueues_automatic_processing(monkeypatch):
    paper_id = uuid4()
    commits = []
    refreshed = []
    added = []
    queued = []

    async def fake_duplicate(_self, _paper):
        return None

    class _Session:
        def add(self, item):
            item.id = paper_id
            item.created_at = SimpleNamespace(isoformat=lambda: "2026-06-13T00:00:00")
            added.append(item)

        async def commit(self):
            commits.append(True)

        async def refresh(self, item):
            refreshed.append(item)

    class _Task:
        id = "task-1"

    class _ProcessTask:
        def delay(self, pid):
            queued.append(pid)
            return _Task()

    monkeypatch.setattr(PaperIngestionService, "check_duplicate", fake_duplicate)
    monkeypatch.setattr(paper_tasks, "process_paper_pipeline", _ProcessTask())

    service = PaperIngestionService(_Session())
    paper, is_new = await service.ingest_paper(
        _paper(source="arxiv", remote_id="2606.00001", arxiv_id="2606.00001", pdf_url="https://arxiv.org/pdf/2606.00001"),
        auto_download=False,
        imported_by_user=SimpleNamespace(id=uuid4(), username="gst"),
    )

    assert is_new is True
    assert paper is added[0]
    assert commits
    assert refreshed == [paper]
    assert queued == [str(paper_id)]
    pipeline = paper.metadata_json[paper_processing_pipeline.PIPELINE_METADATA_KEY]
    assert "full_text" in pipeline["queued_steps"]
    assert "visual_evidence" in pipeline["queued_steps"]


def test_paper_imported_by_user_matches_id_and_username_fallback():
    user_id = uuid4()
    user = SimpleNamespace(id=str(user_id), username="gst")

    assert papers_api._paper_imported_by_user(
        SimpleNamespace(imported_by_user_id=user_id, imported_by_username="other"),
        user,
    )
    assert papers_api._paper_imported_by_user(
        SimpleNamespace(imported_by_user_id=None, imported_by_username="gst"),
        user,
    )
    assert not papers_api._paper_imported_by_user(
        SimpleNamespace(imported_by_user_id=None, imported_by_username="other"),
        user,
    )


@pytest.mark.asyncio
async def test_bibtex_import_enqueues_processing_for_created_papers(monkeypatch):
    added = []
    commits = []
    refreshed = []
    enqueued = []

    class _Upload:
        async def read(self):
            return b"@article{numpro,title={Number it},author={A and B},year={2024},eprint={2411.10332v3}}"

    class _Rows:
        def scalar_one_or_none(self):
            return None

    class _Session:
        async def execute(self, _statement):
            return _Rows()

        def add(self, paper):
            paper.id = uuid4()
            paper.metadata_json = paper.metadata_json or {}
            added.append(paper)

        async def commit(self):
            commits.append(True)

        async def refresh(self, paper):
            refreshed.append(paper)

    async def fake_enqueue(_self, paper):
        enqueued.append(str(paper.id))

    monkeypatch.setattr(papers_api.PaperIngestionService, "enqueue_processing", fake_enqueue)

    result = await papers_api.import_bibtex(_Upload(), db=_Session(), user=SimpleNamespace(id=uuid4(), username="gst"))

    assert result == {"imported": 1, "skipped": 0}
    assert len(added) == 1
    assert commits
    assert refreshed == added
    assert enqueued == [str(added[0].id)]


@pytest.mark.asyncio
async def test_zotero_import_enqueues_processing_for_created_papers(monkeypatch):
    added = []
    enqueued = []

    class _Upload:
        async def read(self):
            return b"Title,Author,Publication Year,DOI,Abstract Note\nTemporal Grounding,Alice; Bob,2024,10.1/test,Abstract"

    class _Rows:
        def scalar_one_or_none(self):
            return None

    class _Session:
        async def execute(self, _statement):
            return _Rows()

        def add(self, paper):
            paper.id = uuid4()
            paper.metadata_json = paper.metadata_json or {}
            added.append(paper)

        async def commit(self):
            return None

        async def refresh(self, paper):
            return None

    async def fake_enqueue(_self, paper):
        enqueued.append(str(paper.id))

    monkeypatch.setattr(papers_api.PaperIngestionService, "enqueue_processing", fake_enqueue)

    result = await papers_api.import_zotero_csv(_Upload(), db=_Session(), user=SimpleNamespace(id=uuid4(), username="gst"))

    assert result == {"imported": 1, "skipped": 0}
    assert len(added) == 1
    assert enqueued == [str(added[0].id)]


@pytest.mark.asyncio
async def test_local_search_applies_readiness_importer_source_and_read_status_filters(monkeypatch):
    from app.services.hybrid_search import HybridSearchService

    async def fake_bm25_readiness_status(_self):
        return {"ready": True, "indexed_papers": 0}

    monkeypatch.setattr(HybridSearchService, "bm25_readiness_status", fake_bm25_readiness_status)

    class _CountResult:
        def scalar(self):
            return 0

    class _Rows:
        def all(self):
            return []

    class _PaperResult:
        def scalars(self):
            return _Rows()

    class _Db:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(str(statement))
            if len(self.statements) == 1:
                return _CountResult()
            return _PaperResult()

    db = _Db()
    class _Rows:
        def all(self):
            return []

    class _Result:
        def scalars(self):
            return _Rows()

    class _Db:
        async def execute(self, _statement):
            return _Result()

    response = await papers_api.search_papers(
        q="",
        source="local",
        category=None,
        year_from=None,
        year_to=None,
        page=1,
        page_size=10,
        sort="created_desc",
        search_mode="hybrid",
        owner=None,
        importer="gst",
        local_source="arxiv",
        has_full_text="true",
        has_embedding="false",
        read_status="completed",
        importance_label="important",
        db=db,
        user=SimpleNamespace(id=uuid4(), username="gst"),
    )

    combined_sql = "\n".join(db.statements)
    assert response.total == 0
    assert "papers.imported_by_username" in combined_sql
    assert "papers.source" in combined_sql
    assert "papers.importance_label" in combined_sql
    assert "length(papers.full_text)" in combined_sql
    assert "papers.embedding IS NULL" in combined_sql
    assert "user_papers.read_status" in combined_sql


@pytest.mark.asyncio
async def test_keyword_local_search_filters_by_importance_label(monkeypatch):
    from app.services.hybrid_search import HybridSearchService

    important = SimpleNamespace(
        id=uuid4(), title="important", authors=[], year=2025, abstract="",
        arxiv_id=None, doi=None, source="manual", citation_count=0,
        created_at=SimpleNamespace(isoformat=lambda: "2026-06-08T00:00:00"),
        importance_label="important", importance_note=None,
        imported_by_user_id=None, imported_by_username="gst",
        metadata_json={}, source_url=None, pdf_path=None, full_text=None,
        embedding=None, tags=[],
    )
    interesting = SimpleNamespace(
        id=uuid4(), title="interesting", authors=[], year=2025, abstract="",
        arxiv_id=None, doi=None, source="manual", citation_count=0,
        created_at=SimpleNamespace(isoformat=lambda: "2026-06-08T00:00:00"),
        importance_label="interesting", importance_note=None,
        imported_by_user_id=None, imported_by_username="gst",
        metadata_json={}, source_url=None, pdf_path=None, full_text=None,
        embedding=None, tags=[],
    )

    async def fake_search(_self, query, top_k, mode):
        return [(str(important.id), 1.0), (str(interesting.id), 0.9)]

    async def fake_fetch(_self, scored, category=None, year_from=None, year_to=None):
        return [(important, 1.0), (interesting, 0.9)]

    monkeypatch.setattr(HybridSearchService, "search", fake_search)
    monkeypatch.setattr(HybridSearchService, "fetch_papers", fake_fetch)

    response = await papers_api.search_papers(
        q="retrieval",
        source="local",
        category=None,
        year_from=None,
        year_to=None,
        page=1,
        page_size=10,
        sort="created_desc",
        search_mode="hybrid",
        owner=None,
        importer=None,
        local_source=None,
        has_full_text=None,
        has_embedding=None,
        read_status=None,
        importance_label="interesting",
        db=_EmptyDb(),
        user=None,
    )

    assert [item.title for item in response.items] == ["interesting"]


@pytest.mark.asyncio
async def test_remote_paper_api_forwards_page_offset_and_year_filters(monkeypatch):
    captured = {}

    async def fake_search(**kwargs):
        captured.update(kwargs)
        return [_paper()]

    monkeypatch.setattr(papers_api, "search_scholarly_papers", fake_search)

    response = await papers_api.search_papers(
        q="video grounding",
        source="arxiv",
        category=None,
        year_from=2022,
        year_to=2026,
        page=3,
        page_size=5,
        sort="created_desc",
        search_mode="hybrid",
        owner=None,
        importer=None,
        local_source=None,
        has_full_text=None,
        has_embedding=None,
        read_status=None,
        importance_label=None,
        db=_EmptyDb(),
    )

    assert captured == {
        "query": "video grounding",
        "source": "arxiv",
        "max_results": 5,
        "start": 10,
        "category": None,
        "year_from": 2022,
        "year_to": 2026,
    }
    assert response.items[0].remote_id == "W123"


@pytest.mark.asyncio
async def test_scholarly_orchestrator_forwards_offset_to_arxiv(monkeypatch):
    captured = {}
    result = _paper(source="arxiv", remote_id="2601.00001", arxiv_id="2601.00001")

    async def fake_arxiv(**kwargs):
        captured.update(kwargs)
        return [result]

    monkeypatch.setattr("app.services.paper_search.arxiv_service.search", fake_arxiv)

    papers = await search_scholarly_papers(
        "video grounding",
        source="arxiv",
        max_results=5,
        start=15,
        year_from=2020,
        year_to=2026,
    )

    assert papers == [result]
    assert captured["start"] == 15
    assert captured["year_from"] == 2020
    assert captured["year_to"] == 2026
