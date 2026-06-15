## Why

arXiv-first Research Scout now preserves PDFs and enriches metadata from Semantic Scholar/OpenAlex, but affiliation coverage remains incomplete when provider metadata is missing. Many arXiv PDFs show author institutions on the first page, so Research Scout should extract conservative institution evidence from that page before declaring affiliations unknown.

## What Changes

- Add bounded arXiv PDF first-page text extraction for arXiv-enriched discovery.
- Extract institution-like affiliation lines from the first page using conservative heuristics.
- Merge extracted affiliations into arXiv candidates only when provider institutions are missing or incomplete.
- Record provenance as `pdf_first_page` with a short evidence snippet.
- Surface PDF-first-page affiliation evidence on Research Scout candidate cards.

## Capabilities

### New Capabilities
- `pdf-first-page-affiliation-extraction`: Scholarly discovery can extract visible affiliation evidence from the first page of arXiv PDFs.

### Modified Capabilities
- `arxiv-first-enriched-discovery`: arXiv-first enriched candidates can include PDF first-page affiliation provenance.
- `chat-research-scout-evaluation`: Research Scout displays PDF-derived affiliation evidence when available.

## Impact

- Backend: `backend/app/services/paper_search.py`, `backend/app/api/chat_sessions.py`.
- Frontend: `frontend/src/pages/ChatPage.tsx`, scoped Research Scout styles.
- Tests: `frontend/tests/chat-research-scout-contract.test.mjs`.
- No database migration is required.
