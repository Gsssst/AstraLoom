"""Bounded CVF OpenAccess discovery for conference paper candidates."""

from __future__ import annotations

import asyncio
import logging
import re
from html import unescape
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.services.paper_search import PaperResult

logger = logging.getLogger(__name__)

CVF_BASE_URL = "https://openaccess.thecvf.com"
CVF_SUPPORTED_VENUES = {"CVPR", "ICCV", "ECCV"}
CVF_TIMEOUT_SECONDS = 12.0
CVF_CACHE_TTL_SECONDS = 600.0

_CVF_CACHE: dict[tuple[str, int], tuple[float, list[PaperResult]]] = {}


def normalize_cvf_venue(value: str | None) -> str | None:
    venue = re.sub(r"[^A-Za-z]", "", value or "").upper()
    return venue if venue in CVF_SUPPORTED_VENUES else None


def cvf_proceedings_url(venue: str, year: int) -> str:
    return f"{CVF_BASE_URL}/{venue}{year}"


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def _link_for_title_node(title_node: Any, page_url: str) -> tuple[str | None, str | None]:
    source_url = None
    pdf_url = None
    containers = []
    container = title_node if getattr(title_node, "name", None) == "dt" else title_node.find_parent("dt") or title_node.parent
    if container:
        containers.append(container)
        sibling = container.find_next_sibling()
        while sibling and getattr(sibling, "name", None) != "dt":
            containers.append(sibling)
            sibling = sibling.find_next_sibling()
    for item in containers:
        for link in item.find_all("a", href=True):
            label = _clean_text(link.get_text(" ")).lower()
            href = urljoin(page_url, link["href"])
            if "pdf" in label or href.lower().endswith(".pdf"):
                pdf_url = pdf_url or href
            elif "arxiv" not in label and not source_url:
                source_url = source_url or href
    return source_url, pdf_url


def parse_cvf_openaccess_html(html: str, *, venue: str, year: int, page_url: str) -> list[PaperResult]:
    """Parse a CVF OpenAccess proceedings page into normalized paper previews."""

    soup = BeautifulSoup(html or "", "html.parser")
    papers: list[PaperResult] = []
    title_nodes = soup.select("dt.ptitle")
    for title_node in title_nodes:
        title = _clean_text(title_node.get_text(" "))
        if not title:
            continue
        authors_node = title_node.find_next_sibling("dd")
        authors = []
        if authors_node:
            author_text = _clean_text(authors_node.get_text(" "))
            authors = [
                item.strip()
                for item in re.split(r"\s*,\s*|\s+;\s+", author_text)
                if item.strip()
            ]
        source_url, pdf_url = _link_for_title_node(title_node, page_url)
        papers.append(PaperResult(
            title=title,
            authors=authors,
            abstract="",
            year=year,
            source="cvf_openaccess",
            source_url=source_url or page_url,
            pdf_url=pdf_url,
            metadata={
                "remote_id": f"{venue}{year}:{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:96]}",
                "venue": venue,
                "venue_year": year,
                "cvf_page_url": page_url,
                "metadata_provenance": {
                    "venue": "cvf_openaccess",
                    "year": "cvf_openaccess",
                    "source_url": "cvf_openaccess",
                    "pdf": "cvf_openaccess" if pdf_url else None,
                },
                "venue_match": {
                    "requested": [venue],
                    "matched": [venue],
                    "status": "matched",
                    "provenance": "cvf_openaccess",
                },
            },
        ))
    return papers


def _matches_query(paper: PaperResult, query: str) -> bool:
    terms = [
        term.lower()
        for term in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", query or "")
        if term.lower() not in {"paper", "papers", "find", "search", "cvpr", "iccv", "eccv"}
    ]
    if not terms:
        return True
    blob = f"{paper.title} {paper.abstract} {' '.join(paper.authors)}".lower()
    return any(term in blob for term in terms)


async def search_cvf_openaccess(
    *,
    venue: str,
    year: int,
    query: str = "",
    max_results: int = 50,
) -> list[PaperResult]:
    """Search a supported CVF proceedings page and return bounded matches."""

    normalized_venue = normalize_cvf_venue(venue)
    if not normalized_venue:
        return []
    cache_key = (normalized_venue, int(year))
    cached = _CVF_CACHE.get(cache_key)
    if cached and asyncio.get_running_loop().time() - cached[0] < CVF_CACHE_TTL_SECONDS:
        papers = cached[1]
    else:
        page_url = cvf_proceedings_url(normalized_venue, int(year))
        try:
            async with httpx.AsyncClient(timeout=CVF_TIMEOUT_SECONDS, follow_redirects=True) as client:
                response = await client.get(page_url)
                response.raise_for_status()
            papers = parse_cvf_openaccess_html(response.text, venue=normalized_venue, year=int(year), page_url=page_url)
            _CVF_CACHE[cache_key] = (asyncio.get_running_loop().time(), papers)
        except Exception as exc:
            logger.warning("CVF OpenAccess search failed for %s %s: %s", normalized_venue, year, exc)
            return []
    filtered = [paper for paper in papers if _matches_query(paper, query)]
    return filtered[:max(1, int(max_results))]
