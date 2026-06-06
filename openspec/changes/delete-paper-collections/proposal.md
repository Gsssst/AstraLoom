## Why

Users can create custom paper collections, but the paper library does not expose a way to remove collections that are no longer useful. Over time this makes the collection selector noisy and forces users to keep obsolete categories forever.

## What Changes

- Add a visible delete action for user-owned paper collections in the paper library.
- Require confirmation before deleting a collection and clearly state that papers remain in the library.
- Refresh the collection list, selected collection, diagnostics, and visible papers after deletion.
- Preserve owner-scoped behavior: users can delete only their own collections.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-collections-to-research-seeds`: extend personal paper collection management with user-visible collection deletion.

## Impact

- Frontend: `frontend/src/pages/PapersPage.tsx` collection management controls and state refresh.
- Backend: `backend/app/api/folders.py` delete response contract and regression coverage.
- Tests: collection UI contract tests and owner-scoped folder delete tests.
