## Why

Research Scout can fail simple Chinese paper-finding prompts because it sends the raw Chinese/mixed-language request directly to arXiv/Semantic Scholar/OpenAlex. It should first ask the LLM to translate and expand the user's research intent into concise English scholarly queries, then use deterministic fallback only if planning fails.

## What Changes

- Add bounded LLM-driven Research Scout query planning that translates and expands user intent into English scholarly query variants.
- Add deterministic fallback query expansion for planner failure or unavailable LLM.
- Run multiple scholarly searches for a scout request and merge/deduplicate candidates before building cards.
- Preserve the original user query for intent display and evaluation, while using planned queries for retrieval.
- Add tests covering the observed "多模态大模型 memory" request.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `chat-research-scout-evaluation`: Research Scout must plan multilingual paper-discovery prompts into scholarly query variants before retrieval.
- `paper-discovery-search-and-ingest`: Scholarly paper discovery requests can use planned query variants before candidate ranking/ingest actions.

## Impact

- Backend: `backend/app/api/chat_sessions.py`.
- Tests: backend retrieval coordination tests and frontend contract tests.
- No database migration, dependency, or frontend UI schema change.
