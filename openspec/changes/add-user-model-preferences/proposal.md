## Why

The API settings page currently switches `llm_service`'s process-wide active model, so one admin's model choice changes the model used by every user. Multi-user research workspaces need model choice to behave like a user preference while the server still owns API keys and available provider configuration.

## What Changes

- Store each user's preferred LLM provider and model on their user record.
- Change `/settings/api-config` so authenticated users can read, save, and test their own model preference without mutating the global runtime default.
- Resolve LLM calls from the current request's user preference first, then fall back to the server default/runtime selection for background jobs and users without a preference.
- Update the settings UI to describe the model choice as "my model" and remove the admin-only save/test restriction for user preferences.

## Capabilities

### New Capabilities

- `user-model-preferences`: Per-user LLM model preference selection, testing, and request-time resolution.

### Modified Capabilities

- `user-model`: Users persist optional LLM provider/model preference fields.

## Impact

- Backend user ORM model and Alembic migration.
- Backend settings API and LLM service request-context resolution.
- Frontend settings API tab copy, controls, and role gating.
- Backend and frontend regression tests.
