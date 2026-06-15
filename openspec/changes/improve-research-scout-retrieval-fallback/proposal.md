## Why

Research Scout currently plans better English scholarly queries, but it can still return no paper cards for simple prompts when the arXiv-first path is too narrow. This breaks the expected "paper hunter" behavior: users should see ranked candidate papers when scholarly sources have related work, not only suggested keywords.

## What Changes

- Add a Research Scout retrieval fallback strategy inspired by PaperQA2, GPT Researcher, STORM, and AI-Scientist patterns: LLM/planned queries, broad multi-source retrieval, dedupe, and ranked candidate synthesis.
- Keep arXiv/PDF candidates preferred, but broaden to Semantic Scholar/OpenAlex/Google Scholar when arXiv-enriched search returns too few candidates.
- Surface retrieval strategy metadata in the existing tool trace so the user can see arXiv-first search and broad fallback execution.
- Ensure Research Scout does not end with only suggested search terms when non-arXiv scholarly providers returned usable candidates.

## Capabilities

### New Capabilities
- `chat-research-scout-evaluation`: Research Scout candidate discovery, tool trace, cards, constraints, and evaluation behavior.

### Modified Capabilities
- `paper-discovery-search-and-ingest`: Paper discovery search must allow arXiv-preferred but non-arXiv scholarly results in fallback paths.

## Impact

- Backend Research Scout orchestration in `backend/app/api/chat_sessions.py`.
- Paper search result merging and optional ranking behavior in `backend/app/services/paper_search.py`.
- Backend tests for Research Scout retrieval coordination.
- Frontend contract tests for Research Scout tool trace metadata if the response metadata shape changes.
