import pytest

from app.services import web_search


@pytest.fixture(autouse=True)
def _disable_structured_providers(monkeypatch):
    monkeypatch.setattr(web_search.settings, "SEARXNG_API_URL", "")
    monkeypatch.setattr(web_search.settings, "TAVILY_API_KEY", "")
    monkeypatch.setattr(web_search.settings, "EXA_API_KEY", "")
    monkeypatch.setattr(web_search.settings, "BRAVE_SEARCH_API_KEY", "")


BING_HTML = """
<ol id="b_results">
  <li class="b_algo">
    <h2><a href="https://example.com/bing">Video grounding paper</a></h2>
    <div class="b_caption"><p>Video grounding benchmark and temporal reasoning snippet</p></div>
  </li>
</ol>
"""

DUCKDUCKGO_HTML = """
<div class="result">
  <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fddg">DuckDuckGo video grounding paper</a>
  <a class="result__snippet">Video grounding long video understanding snippet</a>
</div>
"""

BING_RSS = """
<rss version="2.0">
  <channel>
    <item>
      <title>RSS video grounding paper</title>
      <link>https://example.com/rss</link>
      <description>Video grounding retrieval snippet</description>
    </item>
  </channel>
</rss>
"""


def test_parse_bing_results_returns_bounded_snippets():
    results = web_search._parse_bing_results(BING_HTML + BING_HTML, max_results=1)

    assert results == ["### Video grounding paper\nVideo grounding benchmark and temporal reasoning snippet\n来源: https://example.com/bing"]


def test_parse_duckduckgo_results_returns_bounded_snippets():
    results = web_search._parse_duckduckgo_results(DUCKDUCKGO_HTML, max_results=1)

    assert results == ["### DuckDuckGo video grounding paper\nVideo grounding long video understanding snippet\n来源: https://example.com/ddg"]


def test_parse_bing_rss_results_returns_structured_items():
    results = web_search._parse_bing_rss_result_items(BING_RSS, max_results=1, query="paper")

    assert results == [web_search.WebSearchResult(
            title="RSS video grounding paper",
            snippet="Video grounding retrieval snippet",
        url="https://example.com/rss",
        provider="bing_rss",
        query="paper",
        rank=0,
    )]


class _FakeResponse:
    def __init__(self, text="", status_code=200, payload=None):
        self.text = text
        self.status_code = status_code
        self.payload = payload or {}

    def json(self):
        return self.payload


class _FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url, headers=None, params=None):
        self.urls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def post(self, url, headers=None, json=None):
        self.urls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.mark.asyncio
async def test_search_web_aggregates_bing_and_duckduckgo(monkeypatch):
    client = _FakeClient([_FakeResponse("<rss></rss>"), _FakeResponse("<html></html>"), _FakeResponse(DUCKDUCKGO_HTML)])
    monkeypatch.setattr(web_search.httpx, "AsyncClient", lambda **kwargs: client)

    result = await web_search.search_web("video grounding", max_results=1, search_depth="quick")

    assert "DuckDuckGo video grounding paper" in result
    assert len(client.urls) == 3
    assert client.urls[0] == "https://www.bing.com/search?q=video%20grounding&format=rss"
    assert client.urls[1] == "https://www.bing.com/search?q=video%20grounding"
    assert client.urls[2] == "https://html.duckduckgo.com/html/?q=video%20grounding"


@pytest.mark.asyncio
async def test_search_web_results_deduplicate_canonical_urls(monkeypatch):
    duplicate_ddg = DUCKDUCKGO_HTML.replace(
        "https%3A%2F%2Fexample.com%2Fddg",
        "https%3A%2F%2Fexample.com%2Fbing%3Futm_source%3Dddg",
    )
    client = _FakeClient([_FakeResponse("<rss></rss>"), _FakeResponse(BING_HTML), _FakeResponse(duplicate_ddg)])
    monkeypatch.setattr(web_search.httpx, "AsyncClient", lambda **kwargs: client)

    results = await web_search.search_web_results("video grounding", max_results=3, search_depth="quick")

    assert [result.url for result in results] == ["https://example.com/bing"]


@pytest.mark.asyncio
async def test_search_web_keeps_successful_provider_when_another_fails(monkeypatch):
    client = _FakeClient([RuntimeError("rss unavailable"), RuntimeError("bing unavailable"), _FakeResponse(DUCKDUCKGO_HTML)])
    monkeypatch.setattr(web_search.httpx, "AsyncClient", lambda **kwargs: client)

    results = await web_search.search_web_results("video grounding", max_results=3, search_depth="quick")

    assert [result.provider for result in results] == ["duckduckgo"]


def test_plan_search_queries_expands_breadth_by_depth():
    assert web_search.plan_search_queries("video grounding", "quick") == ["video grounding"]
    assert len(web_search.plan_search_queries("video grounding", "standard")) == 3
    assert len(web_search.plan_search_queries("video grounding", "deep")) == 5


def test_plan_search_queries_normalizes_chinese_academic_paper_request():
    queries = web_search.plan_search_queries("请给我找10篇关于多模态大模型的论文", "deep")

    assert queries[0] == "多模态大模型"
    assert "multimodal large language model papers" in queries
    assert "MLLM survey" in queries
    assert "vision language model papers" in queries
    assert all("请" not in query for query in queries)
    assert all("10" not in query for query in queries)
    assert all("关于" not in query for query in queries)


def test_query_relevance_terms_ignore_chinese_request_scaffolding():
    terms = web_search._query_relevance_terms("请给我找10篇关于多模态大模型的论文")

    assert "多模态大模型" in terms
    assert "multimodal" in terms
    assert "mllm" in terms
    assert "vision" in terms
    assert "请" not in terms
    assert "给我找" not in terms
    assert "10" not in terms


def test_filter_relevant_results_drops_unrelated_dictionary_pages():
    query = "multimodal large language model memory"
    results = [
        web_search.WebSearchResult(
            title="请_百度百科",
            snippet="请的意思、读音、部首、笔顺。",
            url="https://baike.baidu.com/item/%E8%AF%B7",
            provider="bing_rss",
            query="请",
            rank=0,
        ),
        web_search.WebSearchResult(
            title="Memory-augmented multimodal large language models",
            snippet="A survey of long-context vision language model memory for video understanding.",
            url="https://example.com/mllm-memory",
            provider="bing",
            query=query,
            rank=1,
        ),
    ]

    filtered = web_search.filter_relevant_results(query, results)

    assert [item.title for item in filtered] == ["Memory-augmented multimodal large language models"]
    assert filtered[0].as_reference()["retrieval_query"] == query


def test_filter_relevant_results_drops_chinese_translation_pages_for_academic_query():
    query = "请给我找10篇关于多模态大模型的论文"
    results = [
        web_search.WebSearchResult(
            title="请 - Google 翻译",
            snippet="请的英文翻译、发音和例句。",
            url="https://translate.google.com/?sl=zh-CN&tl=en&text=%E8%AF%B7",
            provider="bing_rss",
            query="请",
            rank=0,
        ),
        web_search.WebSearchResult(
            title="请的意思 - 汉语词典",
            snippet="请字的拼音、部首、笔画和解释。",
            url="https://example.com/chinese/%E8%AF%B7",
            provider="bing_rss",
            query="请",
            rank=1,
        ),
        web_search.WebSearchResult(
            title="A Survey on Multimodal Large Language Models",
            snippet="Recent multimodal large language model and MLLM papers for vision-language reasoning.",
            url="https://example.com/mllm-survey",
            provider="bing",
            query="multimodal large language model papers",
            rank=2,
        ),
    ]

    filtered = web_search.filter_relevant_results(query, results)

    assert [item.title for item in filtered] == ["A Survey on Multimodal Large Language Models"]
    assert filtered[0].as_reference()["retrieval_query"] == "multimodal large language model papers"


@pytest.mark.asyncio
async def test_search_web_prefers_configured_tavily_without_unneeded_html_fallback(monkeypatch):
    client = _FakeClient([_FakeResponse(payload={
        "results": [{
            "title": "Tavily video grounding result",
            "content": "Structured video grounding answer context",
            "url": "https://example.com/tavily",
        }],
    })])
    monkeypatch.setattr(web_search.settings, "TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(web_search.httpx, "AsyncClient", lambda **kwargs: client)

    results = await web_search.search_web_results("video grounding", max_results=1, search_depth="quick")

    assert [result.provider for result in results] == ["tavily"]
    assert client.urls == ["https://api.tavily.com/search"]


@pytest.mark.asyncio
async def test_search_web_fills_sparse_structured_results_with_html_fallback(monkeypatch):
    client = _FakeClient([
        _FakeResponse(payload={
            "results": [{
            "title": "Tavily video grounding result",
            "content": "Structured video grounding answer context",
                "url": "https://example.com/tavily",
            }],
        }),
        _FakeResponse(BING_RSS),
        _FakeResponse(BING_HTML),
        _FakeResponse(DUCKDUCKGO_HTML),
    ])
    monkeypatch.setattr(web_search.settings, "TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(web_search.httpx, "AsyncClient", lambda **kwargs: client)

    results = await web_search.search_web_results("video grounding", max_results=3, search_depth="quick")

    assert [result.provider for result in results] == ["tavily", "bing_rss", "bing"]
    assert len(client.urls) == 4


@pytest.mark.asyncio
async def test_search_web_uses_remaining_sources_when_structured_provider_fails(monkeypatch):
    client = _FakeClient([
        RuntimeError("tavily unavailable"),
        RuntimeError("rss unavailable"),
        _FakeResponse(BING_HTML),
        _FakeResponse(DUCKDUCKGO_HTML),
    ])
    monkeypatch.setattr(web_search.settings, "TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(web_search.httpx, "AsyncClient", lambda **kwargs: client)

    results = await web_search.search_web_results("video grounding", max_results=2, search_depth="quick")

    assert [result.provider for result in results] == ["bing", "duckduckgo"]


def test_available_provider_names_do_not_expose_credentials(monkeypatch):
    monkeypatch.setattr(web_search.settings, "SEARXNG_API_URL", "https://search.example.com")
    monkeypatch.setattr(web_search.settings, "TAVILY_API_KEY", "secret-key")

    names = web_search.available_web_provider_names()

    assert names == ["searxng", "tavily", "bing_fallback", "duckduckgo_fallback"]
    assert "secret-key" not in names
