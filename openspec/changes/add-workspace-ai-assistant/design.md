## Context

Project spaces already expose the research context needed for useful workspace-level assistance: linked papers, research projects, writing projects, dashboard progress, next actions, members, and recent activity. The generic chat feature already has persisted `ChatSession` / `ChatMessage` tables, model routing, references, and non-streaming + streaming send flows. The workspace detail page currently acts as a dashboard and resource binder, but it does not let users ask questions or synthesize next steps from the collected workspace context.

Before coding, similar open-source patterns were checked:
- AnythingLLM uses workspace-level separation for chat history, documents, and memory.
- Onyx/Danswer-style assistants emphasize chatting against selected knowledge collections with permissions.
- Open WebUI knowledge/workspace patterns reinforce keeping generic chat separate from scoped, resource-grounded assistant experiences.

The practical pattern for this project is to add a workspace-scoped assistant that reuses existing chat storage and LLM infrastructure while assembling context from workspace resources.

## Goals / Non-Goals

**Goals:**
- Add a workspace assistant panel on `WorkspaceDetailPage`.
- Persist assistant conversation history per workspace.
- Ground assistant replies in the current workspace summary, linked resources, dashboard state, and recent activity.
- Return references to workspace resources used in the context.
- Enforce workspace membership: members can use read-only assistant chat; non-members cannot access it.
- Keep the first iteration non-destructive and advisory.

**Non-Goals:**
- Do not add a new model provider, new LLM dependency, or `.env` setting.
- Do not build a full multi-agent executor that mutates research projects or writing drafts.
- Do not add bulk resource creation from assistant responses.
- Do not replace the generic `/chat` page or merge workspace assistant sessions into normal chat browsing.
- Do not add a new database table unless implementation proves existing chat metadata is insufficient.

## Decisions

- Reuse `ChatSession` / `ChatMessage` for persistence with `metadata_json.scope = "workspace"` and `metadata_json.workspace_id = <space_id>`.
  - Rationale: existing tables already support sessions, messages, references, timestamps, and cascade delete.
  - Alternative considered: add `workspace_ai_sessions` tables. Deferred because it adds migration surface without a clear first-iteration benefit.

- Add workspace-specific endpoints under `/workspaces/{space_id}/assistant`.
  - Rationale: the frontend can remain anchored in project-space permissions and avoid leaking workspace chats into generic chat session APIs.
  - Alternative considered: use `/chat-sessions` with `extra_context`. Rejected for the first UI because it makes membership checks and workspace scoping easier to bypass accidentally.

- Build assistant context from workspace summary resources rather than broad global RAG.
  - Rationale: the assistant should answer from the space, not from unrelated user/global library material.
  - Alternative considered: combine workspace context with global paper RAG. Deferred until the workspace assistant needs broader literature discovery.

- Keep the backend response non-streaming for the first iteration.
  - Rationale: the workspace page already has a dense dashboard. A reliable request/response assistant is enough to validate value and contract tests.
  - Alternative considered: clone the chat streaming SSE flow. Deferred to reduce UI complexity.

- Return references as lightweight workspace resource references.
  - Rationale: users need to inspect the papers, directions, drafts, or activity behind a response.
  - Alternative considered: citation-level references. Deferred because current workspace summaries do not expose paragraph-level evidence.

## Risks / Trade-offs

- [Risk] Workspace context can become too long for large spaces.
  -> Mitigation: cap included resources per type and include concise title/subtitle/path fields first.

- [Risk] Assistant replies may imply it inspected full paper PDFs or draft content when only summaries were included.
  -> Mitigation: system prompt must state the available context boundaries and require the model to say when more inspection is needed.

- [Risk] Reusing generic chat tables can mix sessions if metadata filters are missed.
  -> Mitigation: workspace endpoints must filter both `metadata_json.scope` and `metadata_json.workspace_id` and contract tests must assert this.

- [Risk] Viewers might trigger future write actions unintentionally.
  -> Mitigation: first iteration is read-only for all roles; later write actions require separate OpenSpec requirements.
