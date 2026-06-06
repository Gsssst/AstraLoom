## Context

The current LLM service wraps LiteLLM's OpenAI-compatible provider and hardcodes `settings.DEEPSEEK_MODEL`, `settings.DEEPSEEK_API_KEY`, and `settings.DEEPSEEK_API_BASE` when the process starts. Existing Settings API responses only display those values. There is no safe browser-side place to enter API keys, and the user wants to provide the new endpoint base URL and API key manually after code changes.

GitHub/reference review:
- LibreChat custom endpoints separate endpoint metadata from sensitive `.env` keys and allow OpenAI-compatible providers through `apiKey`, `baseURL`, and model fields.
- Open WebUI exposes OpenAI-compatible URL/API key configuration so users can connect OpenAI-like endpoints.
- OpenAI's Chat Completions API uses a `model` and `messages` request shape with optional streaming; the user's endpoint is compatible with that surface.

## Goals / Non-Goals

**Goals:**
- Support DeepSeek and a GPT-5.5 OpenAI-compatible endpoint through one LLM service.
- Keep API keys and base URLs in server environment variables.
- Let administrators switch active provider/model from the Settings API tab at runtime.
- Preserve existing chat, paper, writing, and research call sites.

**Non-Goals:**
- Do not store API keys in the frontend or database.
- Do not introduce a database-backed system settings table in this change.
- Do not migrate the app from Chat Completions to the Responses API.
- Do not change embedding generation, which still uses the existing embedding path.

## Decisions

- Use a server-side provider registry.
  - Each option has `provider`, `label`, `model`, `api_base`, `has_api_key`, and `supports_thinking`.
  - DeepSeek reads existing `DEEPSEEK_*` variables.
  - OpenAI-compatible reads `OPENAI_COMPATIBLE_API_BASE`, `OPENAI_COMPATIBLE_API_KEY`, and `OPENAI_COMPATIBLE_MODEL`.
- Use runtime overrides for UI selection.
  - `LLM_PROVIDER` and provider model variables define boot defaults.
  - The Settings API can update the in-process active provider/model without writing `.env`.
  - Restarting the service returns to `.env` defaults unless the user sets `LLM_PROVIDER`.
- Restrict model switching to administrators.
  - GET remains available to authenticated users for visibility.
  - PUT requires admin because it changes global runtime behavior.
- Keep all LLM call sites using `llm_service`.
  - The service resolves active configuration per call, so existing imports continue to work.

## Risks / Trade-offs

- [Risk] Runtime selection is not persisted across restarts. Mitigation: expose env variable names and keep `.env.example` updated for persistent defaults.
- [Risk] Some OpenAI-compatible providers differ in max token parameter support. Mitigation: LiteLLM already has `drop_params=True`, and the endpoint is declared Chat Completions-compatible.
- [Risk] Non-DeepSeek models may not emit `reasoning_content`. Mitigation: thinking streams naturally emit visible content only when no reasoning chunks are present.
