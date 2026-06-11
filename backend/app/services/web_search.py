"""Bounded multi-query web research with structured providers and HTML fallback."""

from __future__ import annotations

import asyncio
import logging
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)

ENGLISH_QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "about",
    "can",
    "could",
    "find",
    "for",
    "from",
    "help",
    "how",
    "latest",
    "me",
    "of",
    "official",
    "on",
    "paper",
    "papers",
    "please",
    "research",
    "show",
    "survey",
    "the",
    "to",
    "what",
    "with",
}

CHINESE_QUERY_STOPWORDS = (
    "请帮我",
    "帮我",
    "请你",
    "请",
    "一下",
    "最新进展",
    "官方资料",
    "论文综述",
    "论文",
    "综述",
    "资料",
    "研究",
    "进展",
    "相关",
    "关于",
    "怎么",
    "如何",
    "什么",
)


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    snippet: str
    url: str
    provider: str
    query: str
    rank: int

    def as_reference(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": "web",
            "provider": self.provider,
            "query": self.query,
            "retrieval_query": self.query,
            "rank": self.rank,
            "snippet": self.snippet,
        }


def _format_result(title: str, snippet: str, link: str) -> str:
    return f"### {title}\n{snippet}\n来源: {link}"


def format_web_context(results: list[WebSearchResult]) -> str:
    return "\n\n".join(
        f"[WEB-{index}] {_format_result(result.title, result.snippet, result.url)}"
        for index, result in enumerate(results, 1)
    )


def _normalize_duckduckgo_link(link: str) -> str:
    if link.startswith("//"):
        link = f"https:{link}"
    parsed = urllib.parse.urlparse(link)
    target = urllib.parse.parse_qs(parsed.query).get("uddg")
    return target[0] if target else link


def _canonical_url(url: str) -> str:
    """Normalize tracking-heavy result URLs for cross-provider deduplication."""
    parsed = urllib.parse.urlparse(url.strip())
    filtered_query = urllib.parse.urlencode([
        (key, value)
        for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"ref", "source", "campaign"}
    ])
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        "",
        filtered_query,
        "",
    ))


def _result_key(result: WebSearchResult) -> str:
    canonical = _canonical_url(result.url)
    if canonical and canonical != "/":
        return canonical
    return re.sub(r"\W+", "", result.title.lower())


def _normalize_relevance_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _query_relevance_terms(query: str) -> set[str]:
    """Extract high-signal terms used to reject obviously unrelated web results."""
    normalized = _normalize_relevance_text(query)
    for stopword in CHINESE_QUERY_STOPWORDS:
        normalized = normalized.replace(stopword, " ")

    terms: set[str] = set()
    for token in re.findall(r"[a-z0-9][a-z0-9_+\-.]{1,}", normalized):
        token = token.strip("_+-.")
        if len(token) >= 2 and token not in ENGLISH_QUERY_STOPWORDS:
            terms.add(token)
            for part in re.split(r"[-_.+]", token):
                if len(part) >= 3 and part not in ENGLISH_QUERY_STOPWORDS:
                    terms.add(part)

    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        if phrase not in CHINESE_QUERY_STOPWORDS:
            terms.add(phrase)
    return terms


def _result_relevance_score(query: str, result: WebSearchResult) -> float:
    terms = _query_relevance_terms(query)
    if not terms:
        return 1.0

    title = _normalize_relevance_text(result.title)
    snippet = _normalize_relevance_text(result.snippet)
    url = _normalize_relevance_text(urllib.parse.unquote(result.url))
    weighted_matches = 0.0
    total_weight = 0.0

    for term in terms:
        weight = 1.0
        if len(term) >= 5 or re.fullmatch(r"[a-z0-9][a-z0-9_+\-.]{3,}", term):
            weight = 1.4
        total_weight += weight
        if term in title:
            weighted_matches += weight * 1.0
        elif term in snippet:
            weighted_matches += weight * 0.75
        elif term in url:
            weighted_matches += weight * 0.5

    return weighted_matches / max(total_weight, 1.0)


def _is_relevant_result(query: str, result: WebSearchResult) -> bool:
    terms = _query_relevance_terms(query)
    if not terms:
        return True
    score = _result_relevance_score(query, result)
    if score >= 0.22:
        return True

    searchable = _normalize_relevance_text(
        " ".join([result.title, result.snippet, urllib.parse.unquote(result.url)])
    )
    long_terms = [term for term in terms if len(term) >= 5]
    return any(term in searchable for term in long_terms)


def filter_relevant_results(query: str, results: list[WebSearchResult]) -> list[WebSearchResult]:
    """Remove search-provider fallbacks that clearly do not match the user's query."""
    if not results:
        return []
    filtered = [result for result in results if _is_relevant_result(query, result)]
    dropped = len(results) - len(filtered)
    if dropped:
        logger.info("Filtered off-topic web results: query=%s dropped=%s kept=%s", query[:80], dropped, len(filtered))
    return filtered


def _parse_bing_result_items(html: str, max_results: int, *, query: str = "") -> list[WebSearchResult]:
    """Parse Bing's standard results page into structured items."""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for selector in ["li.b_algo", "ol#b_results li", ".b_results li"]:
        items = soup.select(selector)
        if items:
            break

    results = []
    for item in items:
        title_el = item.select_one("h2 a") or item.select_one("a[href]")
        snippet_el = item.select_one(".b_caption p") or item.select_one("p")
        if title_el and snippet_el:
            url = title_el.get("href", "")
            if url:
                results.append(WebSearchResult(
                    title=title_el.get_text(strip=True),
                    snippet=snippet_el.get_text(" ", strip=True),
                    url=url,
                    provider="bing",
                    query=query,
                    rank=len(results),
                ))
        if len(results) >= max_results:
            break
    return results


def _parse_duckduckgo_result_items(html: str, max_results: int, *, query: str = "") -> list[WebSearchResult]:
    """Parse DuckDuckGo's HTML results page into structured items."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select(".result"):
        title_el = item.select_one(".result__a")
        snippet_el = item.select_one(".result__snippet")
        if title_el and snippet_el:
            url = _normalize_duckduckgo_link(title_el.get("href", ""))
            if url:
                results.append(WebSearchResult(
                    title=title_el.get_text(strip=True),
                    snippet=snippet_el.get_text(" ", strip=True),
                    url=url,
                    provider="duckduckgo",
                    query=query,
                    rank=len(results),
                ))
        if len(results) >= max_results:
            break
    return results


def _parse_bing_rss_result_items(xml: str, max_results: int, *, query: str = "") -> list[WebSearchResult]:
    """Parse Bing's stable RSS output for zero-configuration fallback."""
    soup = BeautifulSoup(xml, "xml")
    results = []
    for item in soup.select("item"):
        title_el = item.select_one("title")
        link_el = item.select_one("link")
        snippet_el = item.select_one("description")
        url = link_el.get_text(strip=True) if link_el else ""
        if title_el and url:
            results.append(WebSearchResult(
                title=title_el.get_text(strip=True),
                snippet=snippet_el.get_text(" ", strip=True) if snippet_el else "",
                url=url,
                provider="bing_rss",
                query=query,
                rank=len(results),
            ))
        if len(results) >= max_results:
            break
    return results


def _parse_bing_results(html: str, max_results: int) -> list[str]:
    """Compatibility parser returning formatted snippets."""
    return [_format_result(item.title, item.snippet, item.url) for item in _parse_bing_result_items(html, max_results)]


def _parse_duckduckgo_results(html: str, max_results: int) -> list[str]:
    """Compatibility parser returning formatted snippets."""
    return [_format_result(item.title, item.snippet, item.url) for item in _parse_duckduckgo_result_items(html, max_results)]


def _normalized_json_results(
    items: list[dict],
    *,
    provider: str,
    query: str,
    max_results: int,
    snippet_keys: tuple[str, ...] = ("snippet", "content", "description", "text"),
) -> list[WebSearchResult]:
    """Normalize common structured-provider result shapes."""
    results = []
    for item in items:
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or url).strip()
        snippet = next((str(item.get(key) or "").strip() for key in snippet_keys if item.get(key)), "")
        if url and title:
            results.append(WebSearchResult(
                title=title,
                snippet=snippet,
                url=url,
                provider=provider,
                query=query,
                rank=len(results),
            ))
        if len(results) >= max_results:
            break
    return results


def configured_structured_provider_names() -> list[str]:
    """Return enabled structured providers without exposing credentials."""
    providers = []
    if settings.SEARXNG_API_URL.strip():
        providers.append("searxng")
    if settings.TAVILY_API_KEY.strip():
        providers.append("tavily")
    if settings.EXA_API_KEY.strip():
        providers.append("exa")
    if settings.BRAVE_SEARCH_API_KEY.strip():
        providers.append("brave")
    return providers


def available_web_provider_names() -> list[str]:
    """Return the configured primary providers and always-available fallbacks."""
    return [*configured_structured_provider_names(), "bing_fallback", "duckduckgo_fallback"]


def plan_search_queries(query: str, search_depth: str = "standard") -> list[str]:
    """Create bounded deterministic variants inspired by planner-based research agents."""
    base = re.sub(r"\s+", " ", query).strip()
    if not base:
        return []
    limits = {"quick": 1, "standard": 3, "deep": 5}
    limit = limits.get(search_depth, limits["standard"])
    current_year = datetime.now().year
    contains_chinese = bool(re.search(r"[\u4e00-\u9fff]", base))
    suffixes = (
        ["", " 最新进展", " 官方资料", " 论文 综述", f" {current_year}"]
        if contains_chinese
        else ["", " latest developments", " official documentation", " research paper survey", f" {current_year}"]
    )
    return list(dict.fromkeys(f"{base}{suffix}".strip() for suffix in suffixes))[:limit]


async def _search_bing(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    encoded = urllib.parse.quote(query)
    response = await client.get(f"https://www.bing.com/search?q={encoded}", headers=_request_headers())
    if response.status_code != 200:
        logger.warning("Bing search returned status=%s query=%s", response.status_code, query)
        return []
    return _parse_bing_result_items(response.text, max_results, query=query)


async def _search_bing_rss(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    encoded = urllib.parse.quote(query)
    response = await client.get(f"https://www.bing.com/search?q={encoded}&format=rss", headers=_request_headers())
    if response.status_code != 200:
        logger.warning("Bing RSS search returned status=%s query=%s", response.status_code, query)
        return []
    return _parse_bing_rss_result_items(response.text, max_results, query=query)


async def _search_duckduckgo(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    encoded = urllib.parse.quote(query)
    response = await client.get(f"https://html.duckduckgo.com/html/?q={encoded}", headers=_request_headers())
    if response.status_code != 200:
        logger.warning("DuckDuckGo search returned status=%s query=%s", response.status_code, query)
        return []
    return _parse_duckduckgo_result_items(response.text, max_results, query=query)


async def _search_searxng(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    response = await client.get(
        f"{settings.SEARXNG_API_URL.rstrip('/')}/search",
        headers=_request_headers(),
        params={"q": query, "format": "json", "categories": "general"},
    )
    if response.status_code != 200:
        logger.warning("SearXNG search returned status=%s query=%s", response.status_code, query)
        return []
    payload = response.json()
    return _normalized_json_results(payload.get("results", []), provider="searxng", query=query, max_results=max_results)


async def _search_tavily(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    response = await client.post(
        "https://api.tavily.com/search",
        json={
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
        },
    )
    if response.status_code != 200:
        logger.warning("Tavily search returned status=%s query=%s", response.status_code, query)
        return []
    payload = response.json()
    return _normalized_json_results(payload.get("results", []), provider="tavily", query=query, max_results=max_results)


async def _search_exa(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    response = await client.post(
        "https://api.exa.ai/search",
        headers={"x-api-key": settings.EXA_API_KEY, "Content-Type": "application/json"},
        json={
            "query": query,
            "numResults": max_results,
            "contents": {"text": {"maxCharacters": 1000}},
        },
    )
    if response.status_code != 200:
        logger.warning("Exa search returned status=%s query=%s", response.status_code, query)
        return []
    payload = response.json()
    return _normalized_json_results(
        payload.get("results", []),
        provider="exa",
        query=query,
        max_results=max_results,
        snippet_keys=("text", "highlights"),
    )


async def _search_brave(client: httpx.AsyncClient, query: str, max_results: int) -> list[WebSearchResult]:
    response = await client.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"Accept": "application/json", "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY},
        params={"q": query, "count": max_results},
    )
    if response.status_code != 200:
        logger.warning("Brave search returned status=%s query=%s", response.status_code, query)
        return []
    payload = response.json()
    return _normalized_json_results(
        payload.get("web", {}).get("results", []),
        provider="brave",
        query=query,
        max_results=max_results,
    )


def _request_headers() -> dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def _configured_structured_searches():
    searches = []
    if settings.SEARXNG_API_URL.strip():
        searches.append(_search_searxng)
    if settings.TAVILY_API_KEY.strip():
        searches.append(_search_tavily)
    if settings.EXA_API_KEY.strip():
        searches.append(_search_exa)
    if settings.BRAVE_SEARCH_API_KEY.strip():
        searches.append(_search_brave)
    return searches


async def _run_searches(
    client: httpx.AsyncClient,
    queries: list[str],
    searches,
    max_results: int,
) -> list[WebSearchResult]:
    responses = await asyncio.gather(*[
        search(client, planned_query, max_results)
        for planned_query in queries
        for search in searches
    ], return_exceptions=True)
    results = []
    for response in responses:
        if isinstance(response, Exception):
            logger.warning("Web search provider failed: %s", response)
            continue
        results.extend(response)
    return results


def _deduplicate_results(results: list[WebSearchResult]) -> list[WebSearchResult]:
    merged = []
    seen = set()
    for result in results:
        key = _result_key(result)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(result)
    return merged


async def search_web_results(
    query: str,
    max_results: int = 5,
    *,
    search_depth: str = "standard",
) -> list[WebSearchResult]:
    """Prefer configured structured providers and fill gaps with HTML fallback."""
    queries = plan_search_queries(query, search_depth)
    if not queries:
        return []

    async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
        structured_searches = _configured_structured_searches()
        primary = _deduplicate_results(await _run_searches(client, queries, structured_searches, max_results))
        fallback = []
        if len(primary) < max_results:
            fallback = await _run_searches(client, queries, (_search_bing_rss, _search_bing, _search_duckduckgo), max_results)

    merged = filter_relevant_results(query, _deduplicate_results([*primary, *fallback]))

    logger.info(
        "Web research completed: query=%s variants=%s primary_providers=%s unique_results=%s",
        query[:80],
        len(queries),
        configured_structured_provider_names(),
        len(merged),
    )
    return merged[:max_results]


async def search_web(query: str, max_results: int = 5, *, search_depth: str = "standard") -> str:
    """Compatibility wrapper returning a grounded Markdown context string."""
    return format_web_context(await search_web_results(query, max_results, search_depth=search_depth))
