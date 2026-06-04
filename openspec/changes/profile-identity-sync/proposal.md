## Why

Users can update their avatar and display name in settings, but the header account control does not reliably reflect those changes. After refreshing or signing in again, the frontend rebuilds its authentication state from `/api/auth/me`, which currently omits the persisted profile identity fields.

## What Changes

- Return the persisted avatar and display name from the current-user API.
- Add a focused authentication-store action for merging profile updates into the active user.
- Synchronize successful avatar, display-name, and email saves from settings into the global authentication state.
- Add regression coverage for restoring the visible profile identity after login or refresh.

## Capabilities

### New Capabilities
- `profile-identity-sync`: Keep persisted account identity fields synchronized across profile settings, authentication recovery, and the header account control.

### Modified Capabilities

## Impact

- Backend current-user API: `backend/app/api/auth.py`
- Frontend authentication state: `frontend/src/stores/useAuthStore.ts`
- Frontend profile settings: `frontend/src/pages/SettingsPage.tsx`
- Backend regression tests for the current-user response contract
