## Why

The application currently assumes a single DeepSeek V4 Pro-compatible model across all LLM calls. The user has another OpenAI Chat Completions-compatible endpoint and needs to switch the active model from the Settings API panel without exposing API keys in the browser.

## What Changes

- Add an LLM provider registry with DeepSeek and an OpenAI-compatible GPT-5.5 option.
- Read provider credentials and base URLs from environment variables, keeping secrets server-side.
- Add a Settings API update path that lets administrators switch the active provider/model at runtime.
- Update the Settings API tab to show available model options, configuration status, and a save action.
- Document the new `.env` variables for the OpenAI-compatible endpoint.

## Capabilities

### New Capabilities

### Modified Capabilities
- `core-workflow-reliability`: LLM calls must use the currently selected provider/model and still return generated content through the existing chat wrappers.
- `usage-attribution-and-digest-schedule`: Token usage records must attribute calls to the active model instead of always recording the DeepSeek model.

## Impact

- Backend configuration: `backend/app/core/config.py`, `backend/app/services/llm.py`, `backend/app/api/settings.py`.
- Frontend settings UI: `frontend/src/pages/SettingsPage.tsx`.
- Deployment templates: `.env.example`, `docker-compose.yml`.
- Tests for LLM provider selection and Settings API contract.
