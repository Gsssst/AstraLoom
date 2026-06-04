## Context

The chat backend already treats web search as an optional context source. The current Bing request can return HTTP 200 with an alternate HTML layout when a result-count parameter is supplied. The parser then returns an empty string, and mixed retrieval silently becomes knowledge-base-only retrieval.

## Goals / Non-Goals

**Goals:**
- Retrieve usable web snippets despite provider HTML variation.
- Fall back to a second provider when Bing produces no parsable results.
- Make web-search unavailability explicit in the model context.

**Non-Goals:**
- Add a paid search API.
- Change the frontend request contract.
- Guarantee that every search provider is available at all times.

## Decisions

- Remove the Bing `count` query parameter and limit results after parsing.
- Keep provider parsing in small pure functions so HTML fixtures can cover layout changes.
- Use DuckDuckGo HTML as a best-effort fallback when Bing has no usable results or raises an exception.
- Insert a system message when all providers fail so the assistant states that online sources were unavailable instead of implying a complete web search.

## Risks / Trade-offs

- [Risk] Search-provider HTML can change again. → Isolate provider parsers and cover expected layouts with tests.
- [Risk] Both public providers can fail or throttle requests. → Preserve bounded timeout and transparent degradation.
