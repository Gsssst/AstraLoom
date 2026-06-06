## Overview

The backend already has an owner-scoped `DELETE /folders/{folder_id}` route, but the paper library does not expose that capability. This change completes the workflow by adding a deliberate frontend delete action and tightening regression coverage around the delete contract.

## Backend

`DELETE /folders/{folder_id}` remains authenticated and owner-scoped through the existing folder lookup. Deleting a folder removes the folder record and folder-paper membership rows via cascade/delete-orphan behavior, but it does not delete papers or `UserPaper` saved/read state.

The response should include the deleted folder id and a `deleted: true` flag so the UI can reliably update state.

## Frontend

When the user is viewing `source === "collection"`:

- Show a delete button next to the selected collection controls.
- Disable it when no collection is selected or a delete is in progress.
- Open a confirmation modal naming the selected collection and explaining that papers remain in the library.
- On success, remove the deleted collection from local state, clear diagnostics/coverage/recommendation state for that collection, and select the next available collection if one exists.
- If no collections remain, keep the user in the collection view with an empty state.

## Permissions And Safety

The delete action calls only the authenticated folder endpoint and does not expose administrator-only global paper deletion. Failed deletes should surface the backend error and leave local state unchanged.

## Risks

- Accidentally implying papers are deleted. Mitigation: confirmation copy explicitly says only the classification is removed.
- Stale selected collection after deletion. Mitigation: centralize local state update after successful delete and select a remaining collection deterministically.
