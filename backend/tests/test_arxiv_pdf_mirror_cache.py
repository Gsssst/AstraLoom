"""Regression tests for arXiv PDF mirror fallback and persistent cache reuse."""

from types import SimpleNamespace

import httpx
import pytest

from app.api import papers as papers_api
from app.services import arxiv_pdf_cache, report_service
from app.tasks import paper_tasks


PDF_BYTES = b"%PDF-1.7\ncached paper"


def _response(url: str, content: bytes = PDF_BYTES, status: int = 200) -> httpx.Response:
    return httpx.Response(status, content=content, request=httpx.Request("GET", url))


def test_candidate_urls_try_configured_mirrors_before_official(monkeypatch):
    monkeypatch.setattr(arxiv_pdf_cache.settings, "ARXIV_PDF_MIRROR_BASE_URLS", "https://mirror-a.example/pdf, https://mirror-b.example/pdf/")
    monkeypatch.setattr(arxiv_pdf_cache.settings, "ARXIV_PDF_OFFICIAL_BASE_URL", "https://arxiv.org/pdf")

    assert arxiv_pdf_cache.arxiv_pdf_candidate_urls("2606.00001v2") == [
        "https://mirror-a.example/pdf/2606.00001.pdf",
        "https://mirror-b.example/pdf/2606.00001.pdf",
        "https://arxiv.org/pdf/2606.00001.pdf",
    ]


@pytest.mark.asyncio
async def test_async_cache_falls_back_after_invalid_mirror_response(monkeypatch, tmp_path):
    calls = []

    class Client:
        async def get(self, url, **_kwargs):
            calls.append(url)
            return _response(url, b"<html>mirror error</html>") if "mirror" in url else _response(url)

    monkeypatch.setattr(arxiv_pdf_cache.settings, "ARXIV_PDF_MIRROR_BASE_URLS", "https://mirror.example/pdf")
    monkeypatch.setattr(arxiv_pdf_cache.settings, "ARXIV_PDF_OFFICIAL_BASE_URL", "https://arxiv.org/pdf")

    resolved = await arxiv_pdf_cache.ensure_cached_arxiv_pdf("2606.00001", client=Client(), cache_dir=str(tmp_path))

    assert calls == [
        "https://mirror.example/pdf/2606.00001.pdf",
        "https://arxiv.org/pdf/2606.00001.pdf",
    ]
    assert resolved.cache_hit is False
    assert resolved.source_url == "https://arxiv.org/pdf/2606.00001.pdf"
    assert (tmp_path / "2606.00001.pdf").read_bytes() == PDF_BYTES


@pytest.mark.asyncio
async def test_async_cache_hit_avoids_upstream_request(tmp_path):
    cache_file = tmp_path / "2606.00001.pdf"
    cache_file.write_bytes(PDF_BYTES)

    class Client:
        async def get(self, *_args, **_kwargs):
            raise AssertionError("cache hit must not contact upstream")

    resolved = await arxiv_pdf_cache.ensure_cached_arxiv_pdf("2606.00001v3", client=Client(), cache_dir=str(tmp_path))

    assert resolved.cache_hit is True
    assert resolved.path == str(cache_file)


@pytest.mark.asyncio
async def test_proxy_serves_cached_pdf_without_upstream_request(monkeypatch, tmp_path):
    cache_file = tmp_path / "2606.00001.pdf"
    cache_file.write_bytes(PDF_BYTES)
    monkeypatch.setattr(arxiv_pdf_cache.settings, "ARXIV_PDF_CACHE_DIR", str(tmp_path))

    response = await papers_api.proxy_pdf("2606.00001")

    assert response.path == str(cache_file)
    assert response.headers["x-pdf-cache"] == "HIT"


@pytest.mark.asyncio
async def test_full_text_parser_reuses_cached_pdf_and_persists_path(monkeypatch, tmp_path):
    cache_file = tmp_path / "2606.00001.pdf"
    cache_file.write_bytes(PDF_BYTES)
    paper = SimpleNamespace(id="paper-1", arxiv_id="2606.00001", abstract="摘要", full_text=None, pdf_path=None)
    persisted = {}

    async def fake_cache(_arxiv_id):
        return arxiv_pdf_cache.CachedArxivPdf(str(cache_file), "2606.00001", None, True)

    def fake_extract(path):
        assert path == str(cache_file)
        return "Introduction\n" + "grounded text " * 60

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, statement):
            persisted["statement"] = statement

        async def commit(self):
            persisted["committed"] = True

    monkeypatch.setattr(report_service, "ensure_cached_arxiv_pdf", fake_cache)
    monkeypatch.setattr(report_service, "_extract_pdf_text", fake_extract)
    monkeypatch.setattr("app.db.session.AsyncSessionLocal", Session)

    result = await report_service._download_and_parse_full_text(paper)

    assert result.startswith("Introduction")
    assert paper.pdf_path == str(cache_file)
    assert persisted["committed"] is True


def test_invalid_arxiv_identifier_is_rejected():
    with pytest.raises(ValueError):
        arxiv_pdf_cache.normalize_arxiv_id("../../etc/passwd")


def test_celery_download_task_reuses_shared_cache_service(monkeypatch, tmp_path):
    cached = arxiv_pdf_cache.CachedArxivPdf(
        path=str(tmp_path / "2606.00001.pdf"),
        arxiv_id="2606.00001",
        source_url=None,
        cache_hit=True,
    )
    calls = []

    def fake_cache(arxiv_id, *, cache_dir=None):
        calls.append((arxiv_id, cache_dir))
        return cached

    monkeypatch.setattr(arxiv_pdf_cache, "ensure_cached_arxiv_pdf_sync", fake_cache)

    result = paper_tasks.download_paper.run("2606.00001")

    assert result["cache_hit"] is True
    assert result["filepath"] == cached.path
    assert calls == [("2606.00001", None)]
