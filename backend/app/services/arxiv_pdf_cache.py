"""Shared arXiv PDF mirror fallback and persistent cache."""

import asyncio
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)
PDF_SIGNATURE = b"%PDF-"
ARXIV_ID_PATTERN = re.compile(
    r"^(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[a-z-]+)?/\d{7})(?:v\d+)?$",
    re.IGNORECASE,
)
_download_locks: dict[str, asyncio.Lock] = {}


class ArxivPdfCacheError(RuntimeError):
    """Raised when no valid PDF can be resolved for an arXiv identifier."""


@dataclass(frozen=True)
class CachedArxivPdf:
    path: str
    arxiv_id: str
    source_url: Optional[str]
    cache_hit: bool


def normalize_arxiv_id(arxiv_id: str) -> str:
    """Validate and normalize an arXiv identifier for upstream and filesystem use."""

    normalized = (arxiv_id or "").strip().removesuffix(".pdf")
    if not ARXIV_ID_PATTERN.fullmatch(normalized):
        raise ValueError("Invalid arXiv identifier")
    return re.sub(r"v\d+$", "", normalized, flags=re.IGNORECASE)


def arxiv_pdf_candidate_urls(arxiv_id: str) -> list[str]:
    """Build ordered mirror candidates followed by the official origin."""

    clean_id = normalize_arxiv_id(arxiv_id)
    encoded_id = quote(clean_id, safe="/")
    return [f"{base_url}/{encoded_id}.pdf" for base_url in settings.arxiv_pdf_base_urls]


def arxiv_pdf_cache_path(arxiv_id: str, cache_dir: Optional[str] = None) -> str:
    """Return the deterministic cache path for an arXiv identifier."""

    clean_id = normalize_arxiv_id(arxiv_id)
    filename = f"{clean_id.replace('/', '--')}.pdf"
    return str(Path(cache_dir or settings.ARXIV_PDF_CACHE_DIR) / filename)


def is_valid_cached_pdf(path: str) -> bool:
    """Return whether a path contains a cached PDF signature."""

    try:
        with open(path, "rb") as handle:
            return handle.read(len(PDF_SIGNATURE)) == PDF_SIGNATURE
    except OSError:
        return False


def _atomic_write_pdf(path: str, content: bytes) -> None:
    if not content.startswith(PDF_SIGNATURE):
        raise ArxivPdfCacheError("Upstream response is not a PDF")
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".arxiv-pdf-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def ensure_cached_arxiv_pdf(
    arxiv_id: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
    cache_dir: Optional[str] = None,
) -> CachedArxivPdf:
    """Resolve one cached arXiv PDF asynchronously, downloading on cache miss."""

    clean_id = normalize_arxiv_id(arxiv_id)
    path = arxiv_pdf_cache_path(clean_id, cache_dir)
    if is_valid_cached_pdf(path):
        return CachedArxivPdf(path=path, arxiv_id=clean_id, source_url=None, cache_hit=True)

    lock = _download_locks.setdefault(path, asyncio.Lock())
    async with lock:
        if is_valid_cached_pdf(path):
            return CachedArxivPdf(path=path, arxiv_id=clean_id, source_url=None, cache_hit=True)

        owns_client = client is None
        active_client = client or httpx.AsyncClient(
            timeout=settings.ARXIV_PDF_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
        errors: list[str] = []
        try:
            for url in arxiv_pdf_candidate_urls(clean_id):
                try:
                    response = await active_client.get(url, headers={"User-Agent": "AstraLoom/1.0"})
                    response.raise_for_status()
                    _atomic_write_pdf(path, response.content)
                    logger.info("arXiv PDF cached: %s <- %s", clean_id, url)
                    return CachedArxivPdf(path=path, arxiv_id=clean_id, source_url=url, cache_hit=False)
                except Exception as exc:
                    errors.append(f"{url}: {exc}")
                    logger.warning("arXiv PDF candidate failed (%s): %s", url, exc)
        finally:
            if owns_client:
                await active_client.aclose()

    raise ArxivPdfCacheError(f"No valid arXiv PDF source for {clean_id}: {'; '.join(errors)}")


def ensure_cached_arxiv_pdf_sync(arxiv_id: str, *, cache_dir: Optional[str] = None) -> CachedArxivPdf:
    """Resolve one cached arXiv PDF synchronously for Celery workers."""

    clean_id = normalize_arxiv_id(arxiv_id)
    path = arxiv_pdf_cache_path(clean_id, cache_dir)
    if is_valid_cached_pdf(path):
        return CachedArxivPdf(path=path, arxiv_id=clean_id, source_url=None, cache_hit=True)

    errors: list[str] = []
    for url in arxiv_pdf_candidate_urls(clean_id):
        try:
            request = Request(url, headers={"User-Agent": "AstraLoom/1.0"})
            with urlopen(request, timeout=settings.ARXIV_PDF_TIMEOUT_SECONDS) as response:
                _atomic_write_pdf(path, response.read())
            logger.info("arXiv PDF cached: %s <- %s", clean_id, url)
            return CachedArxivPdf(path=path, arxiv_id=clean_id, source_url=url, cache_hit=False)
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            logger.warning("arXiv PDF candidate failed (%s): %s", url, exc)

    raise ArxivPdfCacheError(f"No valid arXiv PDF source for {clean_id}: {'; '.join(errors)}")
