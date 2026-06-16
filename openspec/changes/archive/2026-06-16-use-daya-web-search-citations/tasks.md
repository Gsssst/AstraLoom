## 1. Backend Native Citation Path

- [x] 1.1 Add helpers for Daya/OpenAI-compatible web-search options and `url_citation` annotation extraction.
- [x] 1.2 Route ordinary non-stream chat with compatible-provider web search through native `web_search_options` while preserving local RAG context.
- [x] 1.3 Route ordinary streamed chat with compatible-provider web search through the native citation path and emit a final metadata update.
- [x] 1.4 Keep existing local web retrieval as fallback when native web search fails or returns no usable citations.

## 2. Frontend Citation Metadata

- [x] 2.1 Update streaming metadata handling so later `meta` events patch the active assistant message's references/tool trace.
- [x] 2.2 Label annotation-derived citations as model-used sources in the reference strip.

## 3. Verification

- [x] 3.1 Add backend regression tests for annotation extraction, fallback behavior, and streamed metadata updates.
- [x] 3.2 Run focused backend tests and strict OpenSpec validation.
- [x] 3.3 Commit the completed change with git.
