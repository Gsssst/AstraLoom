## Context

Ordinary chat currently handles web enhancement by running local web retrieval before the LLM call, injecting `[WEB-N]` snippets into the prompt, and returning those retained `WebSearchResult` records as references. That is useful as a fallback, but it can mislead users when displayed references are only search candidates rather than sources the model actually relied on.

Official Daya/OpenAI-compatible guidance uses Chat Completions `web_search_options` and returns source attribution through `message.annotations`, specifically `url_citation` annotations containing a title and URL. OpenAI's current web-search tools follow the same product pattern: final answers carry annotations/citations rather than exposing raw search-result candidates as citations. Mature AI search products such as Perplexica similarly present sources attached to the generated answer rather than every retrieval candidate.

## Goals / Non-Goals

**Goals:**
- Prefer Daya/OpenAI-compatible native web search for ordinary chat when the user enables web search.
- Only show provider-native web references that come from model-returned citation annotations.
- Preserve local RAG retrieval and chat tool traces.
- Preserve the current local web retrieval implementation as a fallback for non-compatible providers, provider errors, or missing provider citations.
- Support streamed chat by sending updated citation metadata after the provider response is available.

**Non-Goals:**
- Replace Research Scout's scholarly paper retrieval pipeline.
- Add a new web search provider dependency.
- Guarantee that every provider returns annotations in streaming chunks.
- Change stored database schemas.

## Design

### Native Daya Web Path

When `web_search=true`, `assistant_mode=general`, and the active provider is `openai-compatible`, the backend will:

1. Build local RAG context with web retrieval disabled so knowledge-base references remain available.
2. Call `llm_service.chat_completion_direct(...)` with `web_search_options`.
3. Extract `message.annotations[*].url_citation` into `source: "web"` references with `citation_source: "model_annotation"`.
4. Store and return only those annotation-derived web references plus any local library/tool references.

The Daya search-depth mapping is:
- `quick` -> `search_context_size: "low"`
- `standard` -> `search_context_size: "medium"`
- `deep` -> `search_context_size: "high"`

### Fallback Path

If the native call fails, or if the provider returns no usable `url_citation` annotations, the backend will log a warning and retry through the existing `_append_retrieval_context(..., web_search_enabled=True)` path. Fallback references will keep their existing provider/retrieval-query metadata and will be labeled as retrieval evidence rather than model annotations.

### Streaming Behavior

The existing OpenAI-compatible streaming path uses Responses API for reasoning summaries and cannot reliably expose Chat Completions annotation metadata. For native web search turns, streamed chat will use a direct non-streaming Chat Completions call, then emit:

1. initial `meta` with model and local references,
2. a `status` event indicating provider-native web search is running,
3. one `content` event containing the final answer,
4. a second `meta` event containing the final annotation-derived references,
5. `saved` and `done`.

This sacrifices token-by-token streaming only for native web-search turns, but keeps the citation contract correct.

### Frontend

The stream parser already accepts repeated `meta` events, but existing streaming assistant messages need to be patched when later metadata arrives. The frontend will update the active streaming assistant message's `references`, `research_scout`, and `tool_trace` whenever a later `meta` event arrives.

Reference labels/tooltips will call out `citation_source: "model_annotation"` as "模型实际引用".

## Risks / Trade-offs

- Native web-search streaming becomes answer-at-once for compatible-provider web turns. This is preferable to showing fabricated or pre-retrieved citations.
- Some providers may support `web_search_options` but omit annotations. The fallback keeps answers functional and visible but labels sources as retrieval evidence.
- Provider-native web search may behave differently from local retrieval for Chinese queries. Existing local fallback remains available if annotations are missing.
