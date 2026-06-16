## Why

Research Scout now has a mode-specific agent loop, but the rest of chat still treats tools as ad hoc retrieval or metadata. To move into the Codex/Claude Code-style second stage, chat needs a reusable, safe tool runtime that can plan, execute, trace, and confirm actions across modes instead of each feature building its own mini-agent.

## What Changes

- Add a generic chat agent tool runtime with typed tool definitions, Pydantic argument validation, observations, trace events, and bounded execution.
- Reuse the Research Scout agent lessons while moving common concepts into shared services.
- Add initial registered tools:
  - `search_papers`: scholarly paper discovery without immediate import side effects.
  - `search_library`: local paper/library retrieval.
  - `import_paper`: side-effect tool that requires explicit user confirmation before execution.
- Stream real tool trace metadata to the chat UI using the existing collapsible trace component.
- Add a confirmation path for side-effect tools so the user can approve importing a specific candidate.
- Preserve current Research Scout behavior while allowing future modes such as reading documents, writing assistant, and skills to reuse the same runtime.

## Capabilities

### New Capabilities

- `chat-agent-tool-runtime`: Shared chat tool registry, execution loop, trace events, confirmation gates, and initial research tools.

### Modified Capabilities

- `chat-retrieval-mode-coordination`: Chat SHALL be able to attach structured tool traces and tool observations to assistant messages beyond Research Scout-specific traces.
- `research-toolbox`: Future research skills and reusable tools SHALL be callable through the shared chat agent runtime rather than bespoke per-page orchestration.

## Impact

- Backend chat services and APIs for tool execution, streaming trace metadata, and confirmation handling.
- Frontend chat trace rendering and action affordances for confirmation-required tools.
- Backend tests for tool validation, side-effect blocking, and tool observations.
- Frontend contract tests for tool traces and confirmation UI.
- No database migration required for the first version unless implementation chooses to persist pending confirmations; persistence can use message metadata if needed.
