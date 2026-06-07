## Why

Project spaces already gather papers, research directions, writing drafts, members, activity, and next actions, but users still need to leave the space and manually reconstruct that context in generic chat. A workspace-scoped AI assistant can turn project spaces into an active research cockpit instead of a passive resource list.

## What Changes

- Add a project-space AI assistant entry point on the workspace detail page.
- Ground assistant responses in the current workspace summary: linked papers, research projects, writing projects, dashboard state, and recent activity.
- Provide quick prompts for high-value workspace tasks: progress summary, evidence gaps, next research plan, and writing outline.
- Persist AI conversation history per workspace, separate from generic chat sessions.
- Preserve workspace role boundaries: all members can ask read-only questions, while write-style follow-up actions remain out of scope for the first iteration.
- Return lightweight references to workspace resources used in a response so users can navigate back to the supporting materials.

## Capabilities

### New Capabilities

- `workspace-ai-assistant`: Defines project-space AI assistant behavior, workspace-grounded context, per-space conversation history, references, and role-aware access.

### Modified Capabilities

## Impact

- Backend workspace/chat APIs for workspace assistant sessions and message sending.
- Workspace service context assembly from already accessible workspace summary resources.
- Frontend workspace detail page with an AI assistant panel, quick prompts, message history, loading/error states, and references.
- Database model/migration for workspace-scoped assistant messages or an equivalent persisted session structure.
- Contract tests for API shape, role access, context assembly, and frontend assistant UI.
- No new model provider, environment variable, or LLM dependency is expected.
