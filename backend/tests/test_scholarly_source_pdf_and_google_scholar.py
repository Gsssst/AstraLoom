"""Regression tests for scholarly-provider reliability and open PDF preservation."""

from types import SimpleNamespace

import httpx
import pytest

from app.api import papers as papers_api
from app.services.paper_ingestion import PaperIngestionService
from app.services.paper_search import (
    ArxivSearchService,
    GoogleScholarService,
    OpenAlexService,
    PaperResult,
    merge_provider_results,
)


ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>https://arxiv.org/abs/2606.00001v1</id>
    <published>2026-06-01T00:00:00Z</published>
    <title>Reliable Video Grounding</title>
    <summary>Evidence grounded retrieval.</summary>
    <author><name>Researcher</name></author>
    <link title="pdf" href="https://arxiv.org/pdf/2606.00001v1" />
  </entry>
</feed>"""


@pytest.mark.asyncio
async def test_arxiv_adapter_tries_fallback_endpoint_after_primary_failure(monkeypatch):
    service = ArxivSearchService()
    calls = []

    async def fake_get(url, **_kwargs):
        calls.append(url)
        if url == "https://primary.example/api":
            raise httpx.ReadTimeout("slow primary")
        return httpx.Response(200, text=ARXIV_XML, request=httpx.Request("GET", url))

    monkeypatch.setattr(service.client, "get", fake_get)
    monkeypatch.setattr("app.services.paper_search.settings.ARXIV_API_BASE", "https://primary.example/api")
    monkeypatch.setattr("app.services.paper_search.settings.ARXIV_API_FALLBACK_BASE", "https://fallback.example/api")
    monkeypatch.setattr("app.services.paper_search.settings.ARXIV_REQUEST_DELAY_SECONDS", 0)

    papers = await service.search("video grounding", max_results=1)

    assert calls == ["https://primary.example/api", "https://fallback.example/api"]
    assert papers[0].source == "arxiv"
    assert papers[0].pdf_url == "https://arxiv.org/pdf/2606.00001v1"
    await service.close()


@pytest.mark.asyncio
async def test_arxiv_adapter_reuses_successful_query_cache(monkeypatch):
    service = ArxivSearchService()
    calls = 0

    async def fake_get(url, **_kwargs):
        nonlocal calls
        calls += 1
        return httpx.Response(200, text=ARXIV_XML, request=httpx.Request("GET", url))

    monkeypatch.setattr(service.client, "get", fake_get)
    monkeypatch.setattr("app.services.paper_search.settings.ARXIV_REQUEST_DELAY_SECONDS", 0)

    first = await service.search("video grounding", max_results=3)
    second = await service.search("video grounding", max_results=8)

    assert first == second
    assert calls == 1
    await service.close()


def test_openalex_parser_preserves_best_open_access_pdf():
    paper = OpenAlexService._parse({
        "id": "https://openalex.org/W123",
        "display_name": "Open paper",
        "authorships": [],
        "ids": {},
        "best_oa_location": {
            "landing_page_url": "https://example.org/paper",
            "pdf_url": "https://example.org/paper.pdf",
        },
        "open_access": {"is_oa": True, "oa_status": "gold"},
    })

    assert paper.pdf_url == "https://example.org/paper.pdf"
    assert paper.source_url == "https://example.org/paper"
    assert paper.metadata["open_access"]["is_oa"] is True


@pytest.mark.asyncio
async def test_google_scholar_adapter_is_optional_without_serpapi_key(monkeypatch):
    service = GoogleScholarService()
    called = False

    async def fake_get(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(service.client, "get", fake_get)
    monkeypatch.setattr("app.services.paper_search.settings.SERPAPI_API_KEY", "")

    assert await service.search("video grounding") == []
    assert called is False
    await service.close()


def test_google_scholar_parser_extracts_pdf_resource():
    paper = GoogleScholarService._parse({
        "result_id": "scholar-1",
        "title": "Scholar paper",
        "link": "https://example.org/landing",
        "snippet": "Abstract preview",
        "publication_info": {"summary": "A Researcher - Venue, 2024", "authors": [{"name": "A Researcher"}]},
        "resources": [{"file_format": "PDF", "link": "https://example.org/paper.pdf"}],
        "inline_links": {"cited_by": {"total": 12}},
    })

    assert paper.source == "google_scholar"
    assert paper.pdf_url == "https://example.org/paper.pdf"
    assert paper.year == 2024
    assert paper.citation_count == 12


def test_comprehensive_merge_interleaves_provider_results():
    def paper(source, title):
        return PaperResult(title=title, authors=[], abstract="", year=2026, source=source)

    merged = merge_provider_results([
        [paper("arxiv", "a1"), paper("arxiv", "a2")],
        [paper("openalex", "o1"), paper("openalex", "o2")],
    ], limit=4)

    assert [item.source for item in merged] == ["arxiv", "openalex", "arxiv", "openalex"]


@pytest.mark.asyncio
async def test_ingestion_persists_remote_open_pdf(monkeypatch):
    added = []

    class Session:
        def add(self, paper):
            added.append(paper)

        async def commit(self):
            return None

        async def refresh(self, _paper):
            return None

    async def no_duplicate(_self, _paper):
        return None

    monkeypatch.setattr(PaperIngestionService, "check_duplicate", no_duplicate)
    paper = PaperResult(
        title="Open paper",
        authors=["Researcher"],
        abstract="Available abstract",
        year=2026,
        source="openalex",
        source_url="https://example.org/paper",
        pdf_url="https://example.org/paper.pdf",
        metadata={"remote_id": "W123"},
    )

    stored, is_new = await PaperIngestionService(Session()).ingest_paper(paper, auto_download=False)

    assert is_new is True
    assert stored is added[0]
    assert stored.metadata_json["pdf_url"] == "https://example.org/paper.pdf"


def test_remote_brief_exposes_open_pdf_and_source_url():
    paper = SimpleNamespace(
        title="Open paper",
        authors=[],
        abstract="Abstract",
        year=2026,
        arxiv_id=None,
        doi=None,
        source="openalex",
        source_url="https://example.org/paper",
        pdf_url="https://example.org/paper.pdf",
        citation_count=0,
        metadata={"remote_id": "W123"},
    )

    brief = papers_api._paper_brief(paper, remote=True)

    assert brief.pdf_url == "https://example.org/paper.pdf"
    assert brief.source_url == "https://example.org/paper"


@pytest.mark.asyncio
async def test_google_scholar_api_explains_missing_serpapi_configuration(monkeypatch):
    monkeypatch.setattr(papers_api.settings, "SERPAPI_API_KEY", "")

    with pytest.raises(papers_api.HTTPException) as exc_info:
        await papers_api.search_papers(
            q="video grounding",
            source="google_scholar",
            category=None,
            year_from=None,
            year_to=None,
            page=1,
            page_size=5,
            sort="created_desc",
            search_mode="hybrid",
            db=SimpleNamespace(),
        )

    assert exc_info.value.status_code == 400
    assert "SERPAPI_API_KEY" in exc_info.value.detail
