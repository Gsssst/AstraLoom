## Why

Research Scout can already find and package candidate papers, but users also need to express venue, author, and institution constraints and compare papers on novelty, relevance, reproducibility, impact, experiment quality, and risk. Without a structured evaluation contract, the assistant can overstate claims or hide missing evidence.

## What Changes

- Extend Research Scout intent metadata with venues, institutions, authors, constraint mode, and evaluation focus.
- Add deterministic, evidence-bound evaluation metadata for each candidate, including score, rationale, evidence snippets, and confidence.
- Update the assistant context so generated recommendations use the structured evaluation instead of unsupported free-form claims.
- Surface constraint matches and compact evaluation scores on Research Scout cards.
- Add tests that lock the new intent and evaluation contract.

## Capabilities

### New Capabilities
- `chat-research-scout-evaluation`: Research Scout can parse scholarly constraints and present evidence-bound candidate evaluations.

### Modified Capabilities
- `paper-discovery-search-and-ingest`: Paper discovery candidates can carry venue/organization-like metadata and evaluation fields for downstream chat actions.

## Impact

- Backend: `backend/app/api/chat_sessions.py` intent extraction, candidate shaping, context formatting, and stream metadata.
- Frontend: `frontend/src/pages/ChatPage.tsx` Research Scout types and card rendering.
- Tests: `frontend/tests/chat-research-scout-contract.test.mjs`.
- OpenSpec: new change artifacts under `openspec/changes/enhance-research-scout-evaluation-rubric/`.
- No database migration or new dependency is required for this optimization.
