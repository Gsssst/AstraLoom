"""Scholarly paper discovery through arXiv, Semantic Scholar, and OpenAlex."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.arxiv_pdf_cache import ensure_cached_arxiv_pdf

logger = logging.getLogger(__name__)
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_ENRICHED_PDF_AFFILIATION_LIMIT = 4
AFFILIATION_KEYWORDS = (
    "university", "institute", "laboratory", "lab", "college", "school", "department",
    "centre", "center", "academy", "research", "google", "deepmind", "microsoft", "meta",
    "openai", "nvidia", "adobe", "amazon", "bytedance", "tencent", "alibaba", "baidu",
    "大学", "学院", "研究院", "实验室", "研究所", "集团", "公司",
)
AFFILIATION_EMAIL_DOMAIN_RE = re.compile(r"@([A-Za-z0-9.-]+\.(?:edu|ac\.[a-z]{2}|edu\.[a-z]{2}|org|com))")


@dataclass
class PaperResult:
    """Normalized paper preview returned by every scholarly provider."""

    title: str
    authors: List[str]
    abstract: str
    year: Optional[int]
    published_at: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    source: str = "arxiv"
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    citation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


def _normalized_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def _clean_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    return doi.lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def canonical_paper_key(paper: PaperResult) -> str:
    """Return the strongest stable identifier available for one scholarly paper."""

    if paper.arxiv_id:
        return f"arxiv:{re.sub(r'v\d+$', '', paper.arxiv_id.lower())}"
    if paper.doi:
        return f"doi:{_clean_doi(paper.doi)}"
    metadata = getattr(paper, "metadata", {}) or {}
    if metadata.get("remote_id"):
        return f"{paper.source}:{metadata['remote_id']}"
    return f"title:{_normalized_title(paper.title)}"


def deduplicate_papers(papers: List[PaperResult], limit: Optional[int] = None) -> List[PaperResult]:
    """Preserve provider order while collapsing canonical scholarly duplicates."""

    seen: set[str] = set()
    unique: List[PaperResult] = []
    for paper in papers:
        keys = []
        if paper.arxiv_id:
            keys.append(f"arxiv:{re.sub(r'v\d+$', '', paper.arxiv_id.lower())}")
        if paper.doi:
            keys.append(f"doi:{_clean_doi(paper.doi)}")
        metadata = getattr(paper, "metadata", {}) or {}
        if metadata.get("remote_id"):
            keys.append(f"{paper.source}:{metadata['remote_id']}")
        if paper.title:
            keys.append(f"title:{_normalized_title(paper.title)}")
        if any(key in seen for key in keys):
            continue
        seen.update(keys)
        unique.append(paper)
        if limit and len(unique) >= limit:
            break
    return unique


def create_remote_ingest_token(paper: PaperResult) -> str:
    """Sign a short-lived server-generated remote preview for reliable ingestion."""

    payload = {
        "issued_at": int(time.time()),
        "paper": {
            "title": paper.title,
            "authors": paper.authors,
            "abstract": (paper.abstract or "")[:12000],
            "year": paper.year,
            "published_at": getattr(paper, "published_at", None),
            "arxiv_id": getattr(paper, "arxiv_id", None),
            "doi": getattr(paper, "doi", None),
            "source": paper.source,
            "source_url": getattr(paper, "source_url", None),
            "pdf_url": getattr(paper, "pdf_url", None),
            "categories": getattr(paper, "categories", []),
            "citation_count": getattr(paper, "citation_count", 0),
            "metadata": getattr(paper, "metadata", {}),
        },
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    ).rstrip(b"=")
    signature = hmac.new(settings.SECRET_KEY.encode(), encoded, hashlib.sha256).hexdigest()
    return f"{encoded.decode()}.{signature}"


def read_remote_ingest_token(token: str, max_age_seconds: int = 1800) -> Optional[PaperResult]:
    """Verify and decode a remote preview token issued by this server."""

    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(settings.SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        padding = "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(encoded + padding))
        if int(time.time()) - int(payload["issued_at"]) > max_age_seconds:
            return None
        return PaperResult(**payload["paper"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


class ArxivSearchService:
    """Bounded asynchronous adapter for the arXiv Atom API."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.ARXIV_SEARCH_TIMEOUT_SECONDS, follow_redirects=True)
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._search_cache: Dict[tuple, tuple[float, List[PaperResult]]] = {}

    async def _rate_limit(self):
        """Serialize arXiv calls and respect the configured provider spacing."""

        async with self._request_lock:
            elapsed = time.monotonic() - self._last_request_at
            delay = max(settings.ARXIV_REQUEST_DELAY_SECONDS - elapsed, 0)
            if delay:
                await asyncio.sleep(delay)
            self._last_request_at = time.monotonic()

    @staticmethod
    def _endpoints() -> List[str]:
        return list(dict.fromkeys(
            endpoint.strip()
            for endpoint in (settings.ARXIV_API_BASE, settings.ARXIV_API_FALLBACK_BASE)
            if endpoint.strip()
        ))

    async def _get(self, params: Dict[str, Any]) -> httpx.Response:
        last_error: Optional[Exception] = None
        for endpoint in self._endpoints():
            try:
                await self._rate_limit()
                response = await self.client.get(
                    endpoint,
                    params=params,
                    timeout=settings.ARXIV_SEARCH_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                return response
            except Exception as exc:
                last_error = exc
                logger.warning("arXiv endpoint failed (%s): %s", endpoint, exc)
        if last_error:
            raise last_error
        raise RuntimeError("No arXiv API endpoint configured")

    @staticmethod
    def _query(query: str, category: Optional[str]) -> str:
        terms = re.findall(r"[\w.-]+", query)
        scholarly_query = " AND ".join(f"all:{term}" for term in terms) or f'all:"{query}"'
        return f"({scholarly_query}) AND cat:{category}" if category else scholarly_query

    @staticmethod
    def _parse_entries(xml_text: str) -> List[PaperResult]:
        papers: List[PaperResult] = []
        root = ET.fromstring(xml_text)
        for entry in root.findall("atom:entry", ATOM_NS):
            title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
            summary = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
            published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
            entry_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
            arxiv_id = entry_id.split("/abs/")[-1] if "/abs/" in entry_id else None
            doi = entry.findtext("arxiv:doi", default="", namespaces=ATOM_NS) or None
            journal_ref = entry.findtext("arxiv:journal_ref", default="", namespaces=ATOM_NS) or None
            comment = entry.findtext("arxiv:comment", default="", namespaces=ATOM_NS) or None
            pdf_url = None
            for link in entry.findall("atom:link", ATOM_NS):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break
            papers.append(PaperResult(
                title=" ".join(title.split()),
                authors=[
                    name.text.strip()
                    for name in entry.findall("atom:author/atom:name", ATOM_NS)
                    if name.text
                ],
                abstract=" ".join(summary.split()),
                year=int(published[:4]) if published[:4].isdigit() else None,
                published_at=published or None,
                arxiv_id=arxiv_id,
                doi=doi,
                source="arxiv",
                source_url=entry_id or None,
                pdf_url=pdf_url,
                categories=[
                    category.get("term", "")
                    for category in entry.findall("atom:category", ATOM_NS)
                    if category.get("term")
                ],
                metadata={
                    "remote_id": arxiv_id,
                    "journal_ref": journal_ref,
                    "comment": comment,
                    "metadata_provenance": {
                        "pdf": "arxiv",
                        "arxiv_id": "arxiv",
                        "doi": "arxiv" if doi else None,
                        "journal_ref": "arxiv" if journal_ref else None,
                        "comment": "arxiv" if comment else None,
                    },
                },
            ))
        return papers

    async def search(
        self,
        query: str,
        max_results: int = 20,
        start: int = 0,
        category: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sort_by: str = "relevance",
    ) -> List[PaperResult]:
        cache_key = (query, start, category, year_from, year_to, sort_by)
        cached = self._search_cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < settings.ARXIV_CACHE_TTL_SECONDS:
            return cached[1][:max_results]
        params = {
            "search_query": self._query(query, category),
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate" if sort_by == "date" else "relevance",
            "sortOrder": "descending",
        }
        response = await self._get(params)
        papers = [
            paper for paper in self._parse_entries(response.text)
            if (not year_from or not paper.year or paper.year >= year_from)
            and (not year_to or not paper.year or paper.year <= year_to)
        ]
        self._search_cache[cache_key] = (time.monotonic(), papers)
        return papers[:max_results]

    async def get_by_id(self, arxiv_id: str) -> Optional[PaperResult]:
        clean_id = re.sub(r"v\d+$", "", arxiv_id)
        try:
            response = await self._get({"id_list": clean_id, "max_results": 1})
            papers = self._parse_entries(response.text)
            return papers[0] if papers else None
        except Exception as exc:
            logger.warning("arXiv ID lookup failed for %s: %s", arxiv_id, exc)
            return None

    async def close(self):
        await self.client.aclose()


class SemanticScholarService:
    """Semantic Scholar Graph API adapter with optional API-key support."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    FIELDS = "title,authors,abstract,year,publicationDate,externalIds,url,citationCount,publicationVenue"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=12.0)
        self._call_count = 0
        self._window_start = time.time()

    def _headers(self) -> Dict[str, str]:
        return {"x-api-key": settings.SEMANTIC_SCHOLAR_API_KEY} if settings.SEMANTIC_SCHOLAR_API_KEY else {}

    async def _rate_limit(self):
        self._call_count += 1
        elapsed = time.time() - self._window_start
        if elapsed > 300:
            self._call_count = 1
            self._window_start = time.time()
        elif self._call_count > 90:
            await asyncio.sleep(300 - elapsed + 5)
            self._call_count = 1
            self._window_start = time.time()

    @staticmethod
    def _parse(item: Dict[str, Any]) -> PaperResult:
        external_ids = item.get("externalIds", {}) or {}
        paper_id = item.get("paperId")
        return PaperResult(
            title=item.get("title", ""),
            authors=[author.get("name", "") for author in (item.get("authors", []) or [])],
            abstract=item.get("abstract", "") or "",
            year=item.get("year"),
            published_at=item.get("publicationDate"),
            arxiv_id=external_ids.get("ArXiv"),
            doi=external_ids.get("DOI"),
            source="semantic_scholar",
            source_url=item.get("url"),
            citation_count=item.get("citationCount", 0) or 0,
            metadata={
                "venue": item.get("publicationVenue"),
                "remote_id": paper_id or external_ids.get("ArXiv"),
            },
        )

    async def search(
        self,
        query: str,
        max_results: int = 20,
        start: int = 0,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[PaperResult]:
        await self._rate_limit()
        params: Dict[str, Any] = {"query": query, "limit": max_results, "offset": start, "fields": self.FIELDS}
        if year_from:
            params["year"] = f"{year_from}-" + (str(year_to) if year_to else "")
        try:
            response = await self.client.get(f"{self.BASE_URL}/paper/search", params=params, headers=self._headers())
            response.raise_for_status()
            return [self._parse(item) for item in response.json().get("data", [])]
        except Exception as exc:
            logger.warning("Semantic Scholar search failed: %s", exc)
            return []

    async def get_by_id(self, paper_id: str) -> Optional[PaperResult]:
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/paper/{paper_id}",
                params={"fields": self.FIELDS},
                headers=self._headers(),
            )
            response.raise_for_status()
            return self._parse(response.json())
        except Exception as exc:
            logger.warning("Semantic Scholar lookup failed for %s: %s", paper_id, exc)
            return None

    async def get_by_arxiv_id(self, arxiv_id: str) -> Optional[PaperResult]:
        return await self.get_by_id(f"ARXIV:{re.sub(r'v\d+$', '', arxiv_id)}")

    async def close(self):
        await self.client.aclose()


class OpenAlexService:
    """Public OpenAlex adapter used as a credential-free scholarly fallback."""

    BASE_URL = "https://api.openalex.org"
    SELECT = "id,doi,title,display_name,publication_year,publication_date,authorships,abstract_inverted_index,primary_location,best_oa_location,open_access,ids,cited_by_count,concepts"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=12.0, follow_redirects=True)

    @staticmethod
    def _abstract(index: Optional[Dict[str, List[int]]]) -> str:
        if not index:
            return ""
        tokens = [(position, token) for token, positions in index.items() for position in positions]
        return " ".join(token for _, token in sorted(tokens))

    @classmethod
    def _parse(cls, item: Dict[str, Any]) -> PaperResult:
        ids = item.get("ids", {}) or {}
        primary_location = item.get("primary_location", {}) or {}
        best_oa_location = item.get("best_oa_location", {}) or {}
        primary_source = primary_location.get("source", {}) or {}
        best_source = best_oa_location.get("source", {}) or {}
        institutions = sorted({
            institution.get("display_name", "")
            for authorship in (item.get("authorships", []) or [])
            for institution in (authorship.get("institutions", []) or [])
            if institution.get("display_name")
        })
        pdf_url = best_oa_location.get("pdf_url") or primary_location.get("pdf_url")
        source_url = best_oa_location.get("landing_page_url") or primary_location.get("landing_page_url") or item.get("id")
        openalex_id = (item.get("id") or "").rsplit("/", 1)[-1]
        return PaperResult(
            title=item.get("display_name") or item.get("title") or "",
            authors=[
                authorship.get("author", {}).get("display_name", "")
                for authorship in (item.get("authorships", []) or [])
            ],
            abstract=cls._abstract(item.get("abstract_inverted_index")),
            year=item.get("publication_year"),
            published_at=item.get("publication_date"),
            arxiv_id=(ids.get("arxiv") or "").rsplit("/", 1)[-1] or None,
            doi=_clean_doi(item.get("doi")),
            source="openalex",
            source_url=source_url,
            pdf_url=pdf_url,
            citation_count=item.get("cited_by_count", 0) or 0,
            metadata={
                "remote_id": openalex_id,
                "openalex_id": openalex_id,
                "venue": best_source.get("display_name") or primary_source.get("display_name"),
                "institutions": institutions,
                "open_access": item.get("open_access", {}) or {},
                "concepts": [concept.get("display_name") for concept in (item.get("concepts", []) or [])[:8]],
            },
        )

    async def search(
        self,
        query: str,
        max_results: int = 20,
        start: int = 0,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[PaperResult]:
        params: Dict[str, Any] = {
            "search": query,
            "per-page": max_results,
            "page": start // max(max_results, 1) + 1,
            "select": self.SELECT,
        }
        filters = []
        if year_from:
            filters.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filters.append(f"to_publication_date:{year_to}-12-31")
        if filters:
            params["filter"] = ",".join(filters)
        if settings.OPENALEX_MAILTO:
            params["mailto"] = settings.OPENALEX_MAILTO
        try:
            response = await self.client.get(f"{self.BASE_URL}/works", params=params)
            response.raise_for_status()
            return [self._parse(item) for item in response.json().get("results", [])]
        except Exception as exc:
            logger.warning("OpenAlex search failed: %s", exc)
            return []

    async def get_by_id(self, openalex_id: str) -> Optional[PaperResult]:
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/works/{openalex_id}",
                params={"select": self.SELECT, **({"mailto": settings.OPENALEX_MAILTO} if settings.OPENALEX_MAILTO else {})},
            )
            response.raise_for_status()
            return self._parse(response.json())
        except Exception as exc:
            logger.warning("OpenAlex lookup failed for %s: %s", openalex_id, exc)
            return None

    async def close(self):
        await self.client.aclose()


class GoogleScholarService:
    """Optional SerpApi-backed Google Scholar adapter; never scrapes Scholar HTML."""

    BASE_URL = "https://serpapi.com/search.json"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=12.0, follow_redirects=True)

    @staticmethod
    def _parse(item: Dict[str, Any]) -> PaperResult:
        publication = item.get("publication_info", {}) or {}
        resources = item.get("resources", []) or []
        pdf_url = next(
            (
                resource.get("link")
                for resource in resources
                if resource.get("link")
                and (
                    str(resource.get("file_format", "")).upper() == "PDF"
                    or str(resource.get("link", "")).lower().endswith(".pdf")
                )
            ),
            None,
        )
        summary = publication.get("summary", "") or ""
        year_match = re.search(r"\b(19|20)\d{2}\b", summary)
        source_url = item.get("link") or pdf_url
        remote_id = item.get("result_id") or hashlib.sha256(
            f"{item.get('title', '')}|{source_url or ''}".encode()
        ).hexdigest()[:24]
        return PaperResult(
            title=item.get("title", ""),
            authors=[
                author.get("name", "")
                for author in (publication.get("authors", []) or [])
                if author.get("name")
            ],
            abstract=item.get("snippet", "") or "",
            year=int(year_match.group()) if year_match else None,
            source="google_scholar",
            source_url=source_url,
            pdf_url=pdf_url,
            citation_count=((item.get("inline_links", {}) or {}).get("cited_by", {}) or {}).get("total", 0) or 0,
            metadata={"remote_id": remote_id, "publication_summary": summary},
        )

    async def search(
        self,
        query: str,
        max_results: int = 20,
        start: int = 0,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[PaperResult]:
        if not settings.SERPAPI_API_KEY.strip():
            return []
        params: Dict[str, Any] = {
            "engine": "google_scholar",
            "q": query,
            "api_key": settings.SERPAPI_API_KEY,
            "start": start,
            "num": min(max_results, 20),
        }
        if year_from:
            params["as_ylo"] = year_from
        if year_to:
            params["as_yhi"] = year_to
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return [self._parse(item) for item in response.json().get("organic_results", [])]
        except Exception as exc:
            logger.warning("SerpApi Google Scholar search failed: %s", exc)
            return []

    async def close(self):
        await self.client.aclose()


arxiv_service = ArxivSearchService()
semantic_scholar_service = SemanticScholarService()
openalex_service = OpenAlexService()
google_scholar_service = GoogleScholarService()


def merge_provider_results(groups: List[List[PaperResult]], limit: int) -> List[PaperResult]:
    """Round-robin provider results so comprehensive discovery stays visibly diverse."""

    interleaved: List[PaperResult] = []
    for index in range(max((len(group) for group in groups), default=0)):
        for group in groups:
            if index < len(group):
                interleaved.append(group[index])
    return deduplicate_papers(interleaved, limit)


def _paper_match_keys(paper: PaperResult) -> set[str]:
    """Return provider-independent keys for safe metadata enrichment."""

    keys: set[str] = set()
    if paper.arxiv_id:
        keys.add(f"arxiv:{re.sub(r'v\d+$', '', paper.arxiv_id.lower())}")
    if paper.doi:
        keys.add(f"doi:{_clean_doi(paper.doi)}")
    normalized = _normalized_title(paper.title)
    if normalized and len(normalized) >= 18:
        keys.add(f"title:{normalized}")
    return keys


def _metadata_provenance(metadata: Dict[str, Any]) -> Dict[str, Any]:
    provenance = metadata.get("metadata_provenance")
    return dict(provenance) if isinstance(provenance, dict) else {}


def _venue_from_metadata(metadata: Dict[str, Any]) -> Optional[str]:
    venue = metadata.get("venue")
    if isinstance(venue, dict):
        return venue.get("name") or venue.get("displayName") or (venue.get("alternate_names") or [None])[0]
    if isinstance(venue, str):
        return venue
    return None


def _institutions_from_metadata(metadata: Dict[str, Any]) -> List[str]:
    institutions = metadata.get("institutions")
    if not isinstance(institutions, list):
        return []
    return [str(item) for item in institutions if item]


def _clean_affiliation_candidate(value: str) -> str:
    cleaned = re.sub(r"\S+@\S+", "", value or "")
    cleaned = re.sub(r"^[\s,;:*\dagger†‡§¶|•·]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:.-")
    cleaned = re.sub(r"\b(abstract|keywords|introduction)\b.*$", "", cleaned, flags=re.IGNORECASE).strip(" ,;:.-")
    return cleaned


def _looks_like_affiliation_line(line: str) -> bool:
    lowered = (line or "").lower()
    if not lowered or len(lowered) < 4 or len(lowered) > 220:
        return False
    if lowered.startswith(("abstract", "keywords", "introduction", "figure ", "table ")):
        return False
    return any(keyword in lowered for keyword in AFFILIATION_KEYWORDS) or bool(AFFILIATION_EMAIL_DOMAIN_RE.search(line))


def extract_affiliations_from_first_page_text(text: str, *, limit: int = 8) -> list[dict[str, str]]:
    """Extract conservative institution evidence from a paper first page."""

    lines = [
        _clean_affiliation_candidate(line)
        for line in re.split(r"[\n\r]+", text or "")
        if _looks_like_affiliation_line(line)
    ]
    domain_lines = []
    for match in AFFILIATION_EMAIL_DOMAIN_RE.finditer(text or ""):
        domain = match.group(1).lower()
        if domain and not any(domain in line.lower() for line in lines):
            domain_lines.append(domain)
    seen: set[str] = set()
    evidence: list[dict[str, str]] = []
    for line in [*lines, *domain_lines]:
        cleaned = _clean_affiliation_candidate(line)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        evidence.append({"institution": cleaned[:160], "evidence": cleaned[:260], "source": "pdf_first_page"})
        if len(evidence) >= limit:
            break
    return evidence


def _extract_first_page_text_sync(path: str) -> str:
    try:
        import fitz

        doc = fitz.open(path)
        try:
            if len(doc) == 0:
                return ""
            return (doc[0].get_text() or "").strip()
        finally:
            doc.close()
    except Exception as fitz_exc:
        logger.debug("fitz first-page extraction failed for %s: %s", path, fitz_exc)
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                return ""
            return (pdf.pages[0].extract_text() or "").strip()
    except Exception as pdfplumber_exc:
        logger.debug("pdfplumber first-page extraction failed for %s: %s", path, pdfplumber_exc)
        return ""


async def enrich_arxiv_pdf_first_page_affiliations(papers: List[PaperResult], limit: int = ARXIV_ENRICHED_PDF_AFFILIATION_LIMIT) -> List[PaperResult]:
    """Enrich top arXiv candidates with first-page affiliation evidence."""

    async with httpx.AsyncClient(timeout=settings.ARXIV_PDF_TIMEOUT_SECONDS, follow_redirects=True) as client:
        async def enrich_one(index: int, paper: PaperResult) -> PaperResult:
            if index >= limit or not paper.arxiv_id or not paper.pdf_url:
                return paper
            try:
                cached = await ensure_cached_arxiv_pdf(paper.arxiv_id, client=client)
                first_page_text = await asyncio.to_thread(_extract_first_page_text_sync, cached.path)
                evidence = extract_affiliations_from_first_page_text(first_page_text)
            except Exception as exc:
                logger.info("arXiv PDF affiliation extraction skipped for %s: %s", paper.arxiv_id, exc)
                return paper
            if not evidence:
                return paper
            metadata = dict(getattr(paper, "metadata", {}) or {})
            existing_institutions = _institutions_from_metadata(metadata)
            extracted_institutions = [item["institution"] for item in evidence]
            merged_institutions = list(dict.fromkeys([*existing_institutions, *extracted_institutions]))
            provenance = _metadata_provenance(metadata)
            metadata["institutions"] = merged_institutions
            provenance["institutions"] = provenance.get("institutions") or "pdf_first_page"
            provenance["pdf_first_page_affiliations"] = "pdf_first_page"
            metadata["metadata_provenance"] = {key: value for key, value in provenance.items() if value}
            metadata["pdf_first_page_affiliations"] = evidence
            metadata["pdf_first_page_text_snippet"] = first_page_text[:900]
            enrichment = dict(metadata.get("enrichment") or {})
            providers = list(enrichment.get("providers") or [])
            if "pdf_first_page" not in providers:
                providers.append("pdf_first_page")
            enrichment.update({"strategy": enrichment.get("strategy") or "arxiv_first", "providers": providers, "matched": True})
            metadata["enrichment"] = enrichment
            return PaperResult(
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                year=paper.year,
                published_at=paper.published_at,
                arxiv_id=paper.arxiv_id,
                doi=paper.doi,
                source=paper.source,
                source_url=paper.source_url,
                pdf_url=paper.pdf_url,
                categories=paper.categories,
                citation_count=paper.citation_count,
                metadata=metadata,
            )

        return await asyncio.gather(*(enrich_one(index, paper) for index, paper in enumerate(papers)))


def _merge_arxiv_with_enrichment(base: PaperResult, enrichments: List[PaperResult]) -> PaperResult:
    """Keep arXiv identity/PDF while copying stronger scholarly metadata."""

    metadata: Dict[str, Any] = dict(getattr(base, "metadata", {}) or {})
    provenance = _metadata_provenance(metadata)
    providers: list[str] = []
    citation_count = int(base.citation_count or 0)
    source_url = base.source_url
    doi = _clean_doi(base.doi)
    venue = _venue_from_metadata(metadata)
    institutions = _institutions_from_metadata(metadata)
    concepts = list(metadata.get("concepts") or []) if isinstance(metadata.get("concepts"), list) else []

    for enrichment in enrichments:
        provider = enrichment.source or "scholarly"
        if provider not in providers:
            providers.append(provider)
        enrichment_metadata = getattr(enrichment, "metadata", {}) or {}
        enrichment_venue = _venue_from_metadata(enrichment_metadata)
        if not venue and enrichment_venue:
            venue = enrichment_venue
            provenance["venue"] = provider
        enrichment_institutions = _institutions_from_metadata(enrichment_metadata)
        if enrichment_institutions:
            merged_institutions = sorted(set([*institutions, *enrichment_institutions]))
            if merged_institutions != institutions:
                institutions = merged_institutions
                provenance["institutions"] = provider
        if not doi and enrichment.doi:
            doi = _clean_doi(enrichment.doi)
            provenance["doi"] = provider
        if int(enrichment.citation_count or 0) > citation_count:
            citation_count = int(enrichment.citation_count or 0)
            provenance["citation_count"] = provider
        if source_url == base.source_url and enrichment.source_url:
            metadata["enriched_source_url"] = enrichment.source_url
            provenance["enriched_source_url"] = provider
        enrichment_concepts = enrichment_metadata.get("concepts")
        if isinstance(enrichment_concepts, list):
            concepts = list(dict.fromkeys([*concepts, *[item for item in enrichment_concepts if item]]))[:8]

    if venue:
        metadata["venue"] = venue
    if institutions:
        metadata["institutions"] = institutions
    if concepts:
        metadata["concepts"] = concepts
    metadata["enrichment"] = {
        "strategy": "arxiv_first",
        "providers": providers,
        "matched": bool(providers),
    }
    metadata["metadata_provenance"] = {key: value for key, value in provenance.items() if value}
    return PaperResult(
        title=base.title,
        authors=base.authors,
        abstract=base.abstract,
        year=base.year,
        published_at=base.published_at,
        arxiv_id=base.arxiv_id,
        doi=doi or base.doi,
        source="arxiv",
        source_url=source_url,
        pdf_url=base.pdf_url,
        categories=base.categories,
        citation_count=citation_count,
        metadata=metadata,
    )


def merge_arxiv_enriched_results(
    arxiv_papers: List[PaperResult],
    enrichment_groups: List[List[PaperResult]],
    limit: int,
) -> List[PaperResult]:
    """Return arXiv-first candidates enriched by matching provider metadata."""

    enrichment_index: Dict[str, List[PaperResult]] = {}
    for group in enrichment_groups:
        for paper in group:
            for key in _paper_match_keys(paper):
                enrichment_index.setdefault(key, []).append(paper)

    enriched: List[PaperResult] = []
    seen_keys: set[str] = set()
    for paper in arxiv_papers:
        keys = _paper_match_keys(paper)
        matches = []
        for key in keys:
            matches.extend(enrichment_index.get(key, []))
        deduped_matches = deduplicate_papers(matches)
        enriched_paper = _merge_arxiv_with_enrichment(paper, deduped_matches)
        canonical = canonical_paper_key(enriched_paper)
        if canonical in seen_keys:
            continue
        seen_keys.add(canonical)
        enriched.append(enriched_paper)
        if len(enriched) >= limit:
            break
    return enriched


async def search_scholarly_papers(
    query: str,
    *,
    source: str = "arxiv",
    max_results: int = 20,
    start: int = 0,
    category: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    venue: Optional[str] = None,
    sort_by: str = "relevance",
) -> List[PaperResult]:
    """Search scholarly providers with bounded fallback and canonical de-duplication."""

    def annotate_venue_filter(papers: List[PaperResult], provider: str, *, filtered: bool = False) -> List[PaperResult]:
        if not venue:
            return papers
        annotated: List[PaperResult] = []
        requested = [venue]
        for paper in papers:
            metadata = dict(getattr(paper, "metadata", {}) or {})
            metadata.setdefault("venue_filter", {
                "requested": requested,
                "provider": provider,
                "filtered": filtered,
            })
            annotated.append(PaperResult(
                title=paper.title,
                authors=paper.authors,
                abstract=paper.abstract,
                year=paper.year,
                published_at=paper.published_at,
                arxiv_id=paper.arxiv_id,
                doi=paper.doi,
                source=paper.source,
                source_url=paper.source_url,
                pdf_url=paper.pdf_url,
                categories=paper.categories,
                citation_count=paper.citation_count,
                metadata=metadata,
            ))
        return annotated

    async def arxiv_results() -> List[PaperResult]:
        try:
            return await arxiv_service.search(
                query=query, max_results=max_results, start=start, category=category,
                year_from=year_from, year_to=year_to, sort_by=sort_by,
            )
        except Exception as exc:
            logger.warning("arXiv search failed, using scholarly fallback: %s", exc)
            return []

    async def semantic_results() -> List[PaperResult]:
        return await semantic_scholar_service.search(
            query=query, max_results=max_results, start=start, year_from=year_from, year_to=year_to,
        )

    async def openalex_results() -> List[PaperResult]:
        return await openalex_service.search(
            query=query, max_results=max_results, start=start, year_from=year_from, year_to=year_to,
        )

    async def google_scholar_results() -> List[PaperResult]:
        return await google_scholar_service.search(
            query=query, max_results=max_results, start=start, year_from=year_from, year_to=year_to,
        )

    if source == "openalex":
        return annotate_venue_filter(deduplicate_papers(await openalex_results(), max_results), "openalex")
    if source == "semantic_scholar":
        return annotate_venue_filter(deduplicate_papers(await semantic_results(), max_results), "semantic_scholar")
    if source == "google_scholar":
        return annotate_venue_filter(deduplicate_papers(await google_scholar_results(), max_results), "google_scholar")
    if source == "cvf_openaccess":
        if not venue:
            return []
        from app.services.cvf_openaccess import normalize_cvf_venue, search_cvf_openaccess

        normalized_venue = normalize_cvf_venue(venue)
        if not normalized_venue:
            return []
        years = [year for year in range(year_from or year_to or 0, (year_to or year_from or 0) + 1) if year]
        if not years:
            return []
        groups = await asyncio.gather(*[
            search_cvf_openaccess(venue=normalized_venue, year=year, query=query, max_results=max_results)
            for year in years
        ])
        return deduplicate_papers([paper for group in groups for paper in group], max_results)
    if source == "arxiv_enriched":
        arxiv_group, semantic_group, openalex_group = await asyncio.gather(
            arxiv_results(),
            semantic_results(),
            openalex_results(),
        )
        enriched = merge_arxiv_enriched_results(arxiv_group, [semantic_group, openalex_group], max_results)
        return annotate_venue_filter(await enrich_arxiv_pdf_first_page_affiliations(enriched), "arxiv_enriched")
    if source in ("all", "scholarly"):
        groups = await asyncio.gather(arxiv_results(), semantic_results(), openalex_results(), google_scholar_results())
        return annotate_venue_filter(merge_provider_results(groups, max_results), "scholarly")
    if source != "arxiv":
        raise ValueError(f"Unknown scholarly source: {source}")

    return annotate_venue_filter(deduplicate_papers(await arxiv_results(), max_results), "arxiv")


async def resolve_remote_paper(source: str, remote_id: str) -> Optional[PaperResult]:
    """Resolve a trusted provider identifier into server-side paper metadata."""

    if source == "arxiv":
        return await arxiv_service.get_by_id(remote_id) or await semantic_scholar_service.get_by_arxiv_id(remote_id)
    if source == "semantic_scholar":
        return await semantic_scholar_service.get_by_id(remote_id)
    if source == "openalex":
        return await openalex_service.get_by_id(remote_id)
    if source == "google_scholar":
        return None
    raise ValueError(f"Unknown scholarly source: {source}")
