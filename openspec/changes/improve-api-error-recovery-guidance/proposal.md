## Why

API failures are now parsed into clearer messages, but several workflows still only show transient toast errors. Users need persistent recovery guidance for failures that often require action, such as network outages, authentication expiry, permission issues, validation failures, timeouts, or upstream model errors.

## What Changes

- Extend the shared frontend API error helper with structured error details: message, severity, category, retryability, and suggested recovery action.
- Keep the existing `getApiErrorMessage` string API intact for current call sites.
- Add persistent failure feedback to the settings API connection test so users can see what failed and what to try next.
- Add focused contract tests for structured error recovery details.

## Capabilities

### New Capabilities

### Modified Capabilities
- `api-error-feedback`: API failure feedback must expose recovery guidance in addition to a concise user-facing message.

## Impact

- `frontend/src/services/apiError.ts`
- `frontend/src/pages/SettingsPage.tsx`
- Frontend API error and settings connection contract tests.
- No backend API, database, or dependency changes.
