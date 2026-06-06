## 1. Backend Provider Selection

- [x] 1.1 Add configurable DeepSeek and OpenAI-compatible provider settings.
- [x] 1.2 Refactor `LLMService` to resolve active provider/model per call and record usage for the active model.
- [x] 1.3 Add Settings API response fields and admin-only update endpoint for runtime model selection.

## 2. Frontend Settings UI

- [x] 2.1 Add model option selection and save behavior to the Settings API tab.
- [x] 2.2 Show server-side configuration status without exposing API keys.

## 3. Deployment Configuration

- [x] 3.1 Document new `.env.example` variables for the OpenAI-compatible endpoint.
- [x] 3.2 Pass new LLM variables through Docker Compose backend services.

## 4. Verification

- [x] 4.1 Add backend tests for provider kwargs, usage model attribution, and Settings API update behavior.
- [x] 4.2 Add frontend contract coverage for the Settings API model selector.
- [x] 4.3 Run targeted backend, frontend, and OpenSpec validation checks.
