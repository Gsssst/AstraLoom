## Why

Chat web enhancement can silently fall back to knowledge-base-only answers when Bing returns a successful HTML response in an alternate layout. Users need reliable web-result retrieval and a clear explanation when external search cannot provide usable sources.

## What Changes

- Parse external search results through dedicated provider-specific functions.
- Use the stable Bing result page and fall back to DuckDuckGo HTML search when Bing yields no usable results.
- Log provider fallback and successful result counts for diagnosis.
- Tell the model when web enhancement was requested but no usable online source was retrieved.
- Add regression tests for parsing, provider fallback, and transparent failure context.

## Capabilities

### New Capabilities
- `web-search-result-reliability`: Web-enhanced chat retrieves usable online results through provider fallback and transparently reports unavailable web context.

### Modified Capabilities

## Impact

- Affects `backend/app/services/web_search.py`, `backend/app/api/chat_sessions.py`, and backend tests.
- No database, API request-shape, or frontend dependency changes.
