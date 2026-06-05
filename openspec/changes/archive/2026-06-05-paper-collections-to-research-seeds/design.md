# Design

## Data Model

Use the existing `Folder` table as the user-owned collection record and add a new `paper_folder_items` join table:

- `folders`: collection metadata (`id`, `name`, `user_id`, optional `parent_id` kept for compatibility).
- `paper_folder_items`: many-to-many user-scoped membership (`folder_id`, `paper_id`, `user_id`).

The join table keeps one paper available in multiple collections and prevents cross-user leakage through a unique `(folder_id, paper_id, user_id)` constraint.

## Backend API

Extend `/api/folders`:

- `GET /folders/`: list user collections with paper counts.
- `POST /folders/`: create a user collection.
- `DELETE /folders/{folder_id}`: delete a collection and memberships.
- `GET /folders/{folder_id}/papers`: list papers in a collection.
- `POST /folders/{folder_id}/papers`: add one or more papers to a collection, creating personal saved state as needed.
- `DELETE /folders/{folder_id}/papers/{paper_id}`: remove a paper from a collection.
- `GET /folders/{folder_id}/paper-ids`: return ids for research seeding.

Paper search uses the existing saved/local retrieval for normal browsing and a dedicated folder paper list when source is `collection`.

## Frontend Flow

Paper library:

- Shows a collection selector and create button.
- Supports a bulk action to add currently selected papers to a collection.
- When a collection is selected, lists only papers in that collection and shows a remove action.

Research page:

- Loads collections in the create modal.
- Lets users pick one or more collections.
- Fetches the collection paper IDs and merges them with manually selected papers before project creation.

## Permissions

All collection APIs require authentication and filter by `user_id`. A user cannot add a paper to another user's collection or list another user's collection.
