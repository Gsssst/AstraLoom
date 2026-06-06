## Why

Several high-traffic pages surface backend and network failures as generic messages such as "失败" or silently swallow them. Users cannot tell whether an action timed out, requires login, lacks permission, failed upstream, or can be retried.

Improving error feedback now will make the existing chat, paper library, research direction, and settings workflows easier to recover from before more features are added.

## What Changes

- Add a shared frontend API error parsing helper that extracts a concise Chinese user-facing message from Axios errors, backend error envelopes, validation details, network failures, and timeouts.
- Replace generic or empty error handling in high-frequency workflows with consistent, actionable feedback.
- Preserve current API contracts and page behavior; this change only improves how failures and loading states are presented.
- Keep streaming chat behavior compatible with existing server-sent error events.

## Capabilities

### New Capabilities
- `api-error-feedback`: Frontend workflows must translate API, auth, permission, timeout, and network failures into clear user-visible feedback.

### Modified Capabilities

## Impact

- `frontend/src/services/api.ts`
- `frontend/src/pages/ChatPage.tsx`
- `frontend/src/pages/PapersPage.tsx`
- `frontend/src/pages/ResearchPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- Focused frontend utility tests where practical.
