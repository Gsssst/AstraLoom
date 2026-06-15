## Why

Research Scout should favor papers with reliable arXiv PDFs because most downstream workflows depend on full-text reading and ingestion. However, arXiv alone is weak for venue and affiliation metadata, so arXiv candidates need enrichment from Semantic Scholar, OpenAlex, and arXiv feed fields.

## What Changes

- Parse additional arXiv Atom metadata such as comments and journal references when available.
- Add an arXiv-first scholarly search mode that keeps arXiv/PDF candidates first and enriches them with Semantic Scholar/OpenAlex metadata by arXiv id, DOI, or title.
- Preserve metadata provenance so the UI can show whether venue/institution evidence came from arXiv, Semantic Scholar, OpenAlex, or is still unknown.
- Update Research Scout to use the arXiv-first enriched source.
- Update tool trace and candidate cards to make arXiv PDF availability and enrichment visible.

## Capabilities

### New Capabilities
- `arxiv-first-enriched-discovery`: Scholarly discovery can prioritize arXiv PDFs while enriching candidates with venue, citation, DOI, and institution metadata from other providers.

### Modified Capabilities
- `chat-research-scout-evaluation`: Research Scout uses enriched arXiv-first candidates and exposes metadata provenance in cards and tool traces.

## Impact

- Backend: `backend/app/services/paper_search.py`, `backend/app/api/chat_sessions.py`.
- Frontend: `frontend/src/pages/ChatPage.tsx`, scoped chat styles.
- Tests: `frontend/tests/chat-research-scout-contract.test.mjs`.
- No database migration is required.
