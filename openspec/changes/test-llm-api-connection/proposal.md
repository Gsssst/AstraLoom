## Why

Users can now configure and switch between DeepSeek and an OpenAI-compatible GPT endpoint, but they still need to open the chat page to discover whether the selected model is reachable or slow. A settings-level connection test makes configuration feedback immediate and safer.

## What Changes

- Add an admin-only API endpoint that sends a tiny prompt to the currently selected LLM and returns success, model identity, latency, and a short response preview.
- Add a "test connection" control to the Settings API tab.
- Surface configuration failures and model call failures through the existing API error feedback path.
- Do not accept or expose API keys from the browser.

## Capabilities

### New Capabilities
- `llm-api-connection-test`: Admin users can verify the active LLM provider from settings before using chat.

### Modified Capabilities

## Impact

- Backend settings API in `backend/app/api/settings.py`.
- LLM service call path in `backend/app/services/llm.py`.
- Settings API tab UI in `frontend/src/pages/SettingsPage.tsx`.
- Backend and frontend regression coverage.
