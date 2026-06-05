## Context

Chat sessions and paper Q&A already share `_append_retrieval_context`, but its web branch calls a one-shot `search_web()` helper and injects an unstructured Markdown string. Bing is attempted first and DuckDuckGo is only used as a fallback, so a superficially successful provider response can prevent broader recall. Web results are not included in the references returned to either frontend.

The design borrows a deliberately small subset of patterns from open research tools:

- GPT Researcher plans sub-queries before collecting and aggregating sourced findings.
- Vane uses a meta-search backend and answers with citations.
- MindSearch emphasizes asynchronous multi-query web search.

The existing deployment has no configured paid search API. The first upgrade therefore uses the existing Bing and DuckDuckGo HTML providers without adding infrastructure or secrets.

## Goals / Non-Goals

**Goals:**

- Improve web recall using bounded query variants and concurrent provider search.
- Return structured, deduplicated web citations to both chat surfaces.
- Keep local knowledge base retrieval and web retrieval independently optional.
- Preserve useful answers when a provider fails.
- Restore a clean full TypeScript build.

**Non-Goals:**

- Implement recursive deep research agents.
- Crawl full web pages or add vector storage for web pages.
- Add paid Tavily, Exa, Brave, or Serper credentials.
- Redesign the existing chat interface.

## Decisions

### Use a structured internal web result model

`web_search.py` will parse providers into a `WebSearchResult` structure containing title, snippet, URL, provider, and originating query. A compatibility wrapper will continue returning formatted context for callers that only need text.

Alternative considered: keep concatenating Markdown strings. Rejected because it prevents reliable deduplication, ranking, and clickable citations.

### Expand query breadth according to retrieval depth

Quick mode will use the original query. Standard and deep modes will add a small number of deterministic variants suitable for current information and academic context. Searches will remain bounded.

Alternative considered: use an LLM query planner for every chat message. Deferred because it adds latency, token cost, and another failure mode. The structured service leaves room for a strategic LLM planner later.

### Aggregate both providers concurrently

For each query variant, Bing and DuckDuckGo will be called concurrently. Individual provider failures will be logged and ignored. Results will be normalized by canonical URL and deduplicated before truncation.

Alternative considered: preserve provider fallback. Rejected because fallback improves availability but not breadth.

### Append local and web references together

The shared retrieval function will preserve existing local references and add web reference objects with `source`, `url`, and `query`. Frontends will open `url` when present and fall back to the arXiv route for local papers.

### Treat TypeScript cleanliness as a build gate

Unused imports and unused state will be removed. Genuine typing/import errors will be corrected with the smallest scoped change. The production build and full `tsc -b` command must both pass.

## Risks / Trade-offs

- [HTML search providers can change markup] -> Keep provider parsers isolated and regression-tested with fixtures.
- [Multi-query search increases network requests] -> Bound variants by search depth and deduplicate before context injection.
- [Deterministic query variants are less adaptive than an LLM planner] -> Keep planning isolated so a strategic planner can be added later without changing API contracts.
- [Some web results may be lower quality] -> Prefer original-query results, deduplicate URLs, expose citations, and instruct the model to distinguish web from local evidence.
