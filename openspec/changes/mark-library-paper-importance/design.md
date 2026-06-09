## Overview

This change adds a library-wide marker to `papers`, not `user_papers`, because the marker is meant to be visible to all users. Personal favorites remain unchanged.

## Data Model

Add nullable columns to `papers`:

- `importance_label`: string enum-like value, nullable. Accepted values are `important` and `interesting`.
- `importance_note`: short text, nullable. Used to explain why the paper was marked.

The label is intentionally small and structured so the UI can show stable badges and future filters can be added without parsing free text.

## API

- Include `importance_label` and `importance_note` in `PaperBrief` and `PaperDetail`.
- Add `PUT /papers/{paper_id}/importance` with body:
  - `label`: `important`, `interesting`, or `null`
  - `note`: optional short string
- Return the updated marker payload.

## Frontend

- Paper list cards show a compact badge near the existing metadata tags.
- Paper detail header shows the same badge and a small control for signed-in users.
- Clearing the marker removes both label and note.

## Permissions

Any authenticated user can set or clear the shared marker. This matches the collaboration intent and keeps the feature lightweight. If moderation is needed later, this can be tightened to admin-only without changing the data model.

## Verification

- Unit tests cover response serialization and marker update behavior.
- Frontend build verifies TypeScript and imports.
- OpenSpec validation covers the changed requirements.
