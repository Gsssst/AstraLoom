## Why

The primary workflow pages still rely heavily on short-lived `message.error` notifications, so failures in search, generation, writing, export, and maintenance flows are easy to miss and often do not explain recovery. Utility pages already expose structured recovery guidance; bringing the same pattern to primary workflows makes failures actionable without changing backend behavior.

## What Changes

- Add a reusable frontend error alert component backed by `getApiErrorDetails`.
- Add persistent dismissible error feedback to `PapersPage`, `ResearchPage`, `ResearchProjectPage`, and `WritingPage`.
- Convert key API failure paths on those pages to set structured error details with recovery, category, retryability, and status.
- Clear stale failure feedback after successful operations where appropriate.
- Add contract coverage for the shared error alert component and primary workflow page adoption.

## Capabilities

### New Capabilities

### Modified Capabilities

- `api-error-feedback`: Primary workflow pages should display persistent structured recovery guidance for important API failures.
- `paper-discovery-search-and-ingest`: Paper library search, import, collection, maintenance, and report operations should surface structured recovery guidance.
- `research-idea-workbench`: Research direction list and project workbench operations should surface structured recovery guidance.
- `writing-workbench-consolidation`: Writing project, generation, citation, export, and grant helper operations should surface structured recovery guidance.

## Impact

- `frontend/src/components/ApiErrorAlert.tsx`
- `frontend/src/pages/PapersPage.tsx`
- `frontend/src/pages/ResearchPage.tsx`
- `frontend/src/pages/ResearchProjectPage.tsx`
- `frontend/src/pages/WritingPage.tsx`
- Frontend contract tests.
- No backend API, database, dependency, or environment changes.
