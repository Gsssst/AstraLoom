## Why

Research Scout still behaves like a fixed query-cleaning pipeline: the backend parses the user request, generates a small set of search strings, runs predetermined providers, then asks the model to summarize. This keeps causing regressions where hard constraints such as year, venue, and institution are parsed but not consistently passed to provider filters or recovery searches.

Mature tool-using agents such as Claude Code, OpenAI function calling applications, OpenHands, and PaperQA2 use a different pattern: the model chooses from declared tools, the application executes validated tool calls, observations are fed back into the model, and the loop continues until there is enough evidence or a bounded stopping condition is reached. Research Scout should adopt that controlled agent loop instead of adding more one-off query-cleaning rules.

## What Changes

- Replace Research Scout's fixed single-pass retrieval orchestration with an agentic, bounded tool loop for paper discovery.
- Add a backend Research Scout tool registry with typed tools for query analysis, arXiv search, Semantic Scholar/OpenAlex search, CVF/OpenAccess venue search, local library search, candidate filtering, ranking, evaluation, and import-ready card preparation.
- Allow the model to decide when to broaden/narrow search queries, retry with aliases, route venue requests to venue-specific sources, and stop when enough validated candidates are available.
- Treat requested year, venue, institution, author, dataset, task, and count as structured constraints that tools receive directly; hard constraints must be enforced before final cards are returned.
- Add CVF/OpenAccess as the primary source for CVPR/ICCV/ECCV-style venue requests, while using arXiv/Semantic Scholar/OpenAlex to enrich PDF, citation, abstract, DOI, and institution metadata.
- Preserve arXiv-first preference for PDF-backed candidates, but no longer rely on arXiv to prove official CVPR/ICCV/ECCV venue membership.
- Surface the actual agent trace in chat: model intent, tool call, validated arguments, result counts, constraint failures, retries, and final stop reason.
- Keep all side-effect tools such as `import_paper`, `add_to_folder`, and `add_to_project` confirmation-gated by the user.

## Capabilities

### New Capabilities
- `research-scout-agentic-discovery`: Agentic Research Scout behavior, tool loop, constraints, candidate cards, evaluations, and trace semantics.

### Modified Capabilities
- `scholarly-source-pdf-and-google-scholar`: Add venue-specific CVF/OpenAccess discovery and metadata preservation for conference paper requests.
- `paper-search`: Ensure year and venue constraints are first-class search parameters, not only ranking hints.
- `chat-retrieval-mode-coordination`: Route Research Scout chat requests through the agent loop and stream observable tool execution state.

## Impact

- Backend:
  - `backend/app/api/chat_sessions.py`
  - new or refactored service modules such as `backend/app/services/research_scout_agent.py`, `backend/app/services/research_scout_tools.py`, and `backend/app/services/cvf_openaccess.py`
  - `backend/app/services/paper_search.py`
  - `backend/app/services/llm.py` if a reusable tool-calling wrapper is added
- Frontend:
  - `frontend/src/pages/ChatPage.tsx`
  - chat/research-scout styles and contract tests
- Tests:
  - backend Research Scout agent loop, tool validation, provider routing, year/venue filtering, and fallback behavior
  - frontend contract coverage for tool traces and candidate card metadata
- External systems:
  - arXiv, Semantic Scholar, OpenAlex, optional SerpApi Google Scholar, and CVF OpenAccess HTML pages
