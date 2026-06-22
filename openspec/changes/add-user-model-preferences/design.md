## Context

The current settings API exposes `/settings/api-config` as an administrator-only switch that calls `llm_service.select_model(...)`. That method writes the runtime selection, so the active model is process-wide. In a multi-user deployment this means an administrator changing the visible settings page changes every user's chat, paper Q&A, writing, and research generation model.

The server already owns API keys and provider availability through environment variables. Users should select from those server-configured options without gaining access to secrets.

## Goals / Non-Goals

**Goals:**

- Persist an optional preferred provider/model per user.
- Let normal authenticated users save and test their own model preference.
- Make all request-scoped LLM calls resolve the current user's saved preference first.
- Preserve server default/runtime selection for background jobs and users without preferences.
- Keep API keys and base URL secrets server-side.

**Non-Goals:**

- Allowing users to enter their own API keys.
- Adding arbitrary custom model definitions from the UI.
- Removing the existing server default/runtime selection mechanism.

## Decisions

- Store preferences directly on `users` as nullable `llm_provider` and `llm_model`.
  - Rationale: This is a small account preference with one active value per user. Keeping it on `users` avoids a separate table and simplifies request-time resolution.
  - Alternative considered: a generic user settings JSON column. That is more flexible but weaker for validation, migration, and direct query/testing.

- Use a request `ContextVar` for the current user's LLM preference.
  - Rationale: Existing token usage attribution already uses request context. The same pattern lets the shared `llm_service` keep its existing call sites while resolving provider/model per request.
  - Alternative considered: threading `user` or `model_preference` through every LLM call. That would touch many chat, paper, writing, and research call sites and is easier to miss.

- Change `/settings/api-config` from a global admin switch to a user preference endpoint.
  - Rationale: The UI label is personal settings, and the reported bug is caused by global mutation. Server defaults still come from env/runtime config for fallback and background work.
  - Alternative considered: add a second endpoint while keeping the current button global. That keeps the footgun visible and does not solve the user's immediate problem.

- Validate preferences against `llm_service.available_options()`.
  - Rationale: Users can only choose configured server providers. The API still never stores or returns API keys.

## Risks / Trade-offs

- [Risk] Existing admin workflow for changing the global runtime model from the settings tab disappears. → Mitigation: server defaults still come from env/runtime config; this UI now matches multi-user expectations.
- [Risk] Some background jobs expected to use a user's preference. → Mitigation: only authenticated request paths get user context; background jobs keep deterministic server defaults until explicitly designed otherwise.
- [Risk] A saved provider becomes unconfigured after env changes. → Mitigation: API responses keep returning available options and validation rejects saving unconfigured providers; calls fall back to server default if the stored preference no longer resolves to a configured option.

## Migration Plan

- Add nullable `llm_provider` and `llm_model` columns to `users`.
- Existing users keep null preferences and therefore continue using the current server default.
- Downgrade drops the two nullable preference columns.
