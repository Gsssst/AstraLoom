## Why

The general chat agent can now plan tool calls, but its useful actions still stop at searching and importing papers. To move Stage 2 forward, the agent needs a small set of library-management tools that let it read local paper evidence and prepare user-confirmed organization actions.

## What Changes

- Add `read_pdf` as a safe read-only chat tool for retrieving bounded local paper evidence from stored full text, abstract, and chunk retrieval.
- Add `add_to_folder` as a side-effect chat tool that adds existing local papers to an existing folder only after explicit confirmation.
- Add `create_research_project` as a side-effect chat tool that creates a research direction/project, optionally linking existing local papers, only after explicit confirmation.
- Teach deterministic fallback to route obvious prompts for reading local PDFs, adding papers to folders, and creating research projects.
- Extend frontend confirmation handling so the existing tool trace UI can confirm the new side-effect tools, not only `import_paper`.
- Keep Research Scout-specific card actions independent from these generic chat tools.

## Capabilities

### New Capabilities

### Modified Capabilities

- `chat-agent-tool-runtime`: The registered tool set expands beyond paper search/import to local evidence reading and confirmed library/project organization actions.
- `llm-tool-planner`: The planner prompt and deterministic fallback can select the expanded safe/side-effect tool set while preserving bounded execution and confirmation gates.

## Impact

- Backend tool schemas and executors in `backend/app/services/chat_agent_tools.py`.
- Chat confirmation API validation in `backend/app/api/chat_sessions.py`.
- Frontend chat trace confirmation copy and accepted side-effect tool names in `frontend/src/pages/ChatPage.tsx`.
- Focused backend tests for tool registration, validation, execution, side-effect confirmation, and deterministic fallback.
- Frontend contract tests for trace confirmation affordances for the expanded tools.
