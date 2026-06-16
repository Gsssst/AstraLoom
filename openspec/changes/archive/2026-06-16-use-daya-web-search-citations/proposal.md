## Why

The current chat web-search path can display pre-retrieved "most relevant" websites even when the model did not actually cite or use them. Daya's OpenAI-compatible Chat Completions API supports native `web_search_options` and returns actual `message.annotations.url_citation` data, so chat citations should use that provider-native grounding when available.

## What Changes

- Prefer provider-native web search for ordinary chat when web enhancement is enabled and the active provider is OpenAI-compatible/Daya.
- Convert Daya/OpenAI-compatible `url_citation` annotations into clickable chat references.
- Keep local knowledge-base retrieval active, but do not inject pre-retrieved web snippets when native provider web search is selected.
- Fall back to the existing local web retrieval stack only when provider-native web search is unavailable, fails, or returns no usable citations.
- Update frontend reference wording so provider annotation citations are distinguishable from local pre-retrieval sources.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `chat-web-research`: web references must distinguish model-used provider citations from pre-retrieved fallback web evidence.

## Impact

- Affects backend chat endpoints in `backend/app/api/chat_sessions.py`.
- Reuses the existing direct OpenAI-compatible helper in `backend/app/services/llm.py`.
- Affects frontend citation labels in `frontend/src/pages/ChatPage.tsx`.
- Adds backend regression coverage for Daya web-search citation extraction, fallback behavior, and streamed metadata updates.
- No database migration or new runtime dependency is expected.
