## Context

The LLM service already supports per-request model selection via `set_request_llm_preference(user)` and `get_active_option()`. Settings API saves `users.llm_provider` and `users.llm_model`, and test calls explicitly set this context.

Paper-detail Q&A endpoints currently accept only `db` as a dependency and therefore never load `get_current_user`. As a result, LLM calls fall back to `llm_service.get_server_default_option()`, which may be DeepSeek even when the current user has selected GPT/OpenAI-compatible.

## Goals / Non-Goals

**Goals:**
- Make paper non-streaming and streaming Q&A use the authenticated user's saved model preference.
- Preserve existing authorization expectations for paper chat history, shares, annotations, and saved papers.
- Keep the change small and avoid touching the LLM provider implementation.

**Non-Goals:**
- Adding per-message model overrides in the paper page UI.
- Changing server default model behavior.
- Changing unauthenticated paper detail browsing.

## Decisions

- Add `user=Depends(get_current_user)` to both paper ask endpoints.
  - Rationale: the frontend already sends `Authorization` for `ask-stream`; paper chat is a personalized feature and history/share endpoints are authenticated.

- Call `set_request_llm_preference(user)` at endpoint entry before context building and generation.
  - Rationale: retrieval and image attachment helpers may call LLM-related utilities; setting the context early keeps behavior consistent.

- Do not call `clear_request_llm_preference()` manually in endpoints.
  - Rationale: the service uses Python `ContextVar`, scoped to the current request task. Existing settings test endpoint already follows this pattern.

## Risks / Trade-offs

- If a user has saved an unconfigured model, `llm_service.get_active_option()` will fall back to server default. This is existing service behavior and should remain.
- If an unauthenticated caller used paper ask before, they will now receive an auth error. The paper page already sends auth headers and paper chat features are user-scoped.
