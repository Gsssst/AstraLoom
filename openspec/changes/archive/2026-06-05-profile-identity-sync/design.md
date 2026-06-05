## Context

The settings page reads profile data from `/api/settings/profile`, while the application header renders the user stored in `useAuthStore`. Login, registration, token refresh, and page reload restore that store through `/api/auth/me`. The database already persists `avatar` and `display_name`, but the current-user endpoint drops them during response construction. Settings also updates its local profile state without consistently merging successful saves into the authentication store.

## Goals / Non-Goals

**Goals:**
- Restore all visible identity fields through `/api/auth/me`.
- Give profile settings one store action for synchronizing successful updates.
- Make header avatar, display name, and account email state react immediately after saves.

**Non-Goals:**
- Change authentication tokens, password handling, or database schema.
- Introduce a separate profile cache.
- Alter the visual design of the settings page or header account chip.

## Decisions

### Return visible identity fields from the existing current-user endpoint
`/api/auth/me` remains the canonical frontend recovery endpoint and will include `avatar` and `display_name`. This keeps login and refresh recovery aligned with the persisted database record without adding another request.

### Merge successful settings responses into the authentication store
`useAuthStore` will expose a small `updateUser` action that merges partial profile fields into the active user. The settings page will call this action only after the backend confirms the save, so the header remains consistent with persisted state.

### Use backend response values after saves
The profile page will replace its local state with the returned profile fields instead of assuming the submitted values were accepted unchanged. Avatar uploads will merge the returned avatar into both local and global state.

## Risks / Trade-offs

- [Large base64 avatars are returned from `/api/auth/me`] → Preserve the existing storage design and response size limit; changing avatar storage is outside this fix.
- [A partial store merge can run before authentication state exists] → Treat it as a no-op when there is no active user.

