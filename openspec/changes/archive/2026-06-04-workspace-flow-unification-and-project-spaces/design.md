# Design

## Data Model

Add two tables:

- `project_spaces`
  - owner user
  - name, description, status, metadata
- `project_space_members`
  - space, user, role

Resource linking starts as metadata-driven to minimize invasive schema changes:

- `resource_links` in `ProjectSpace.metadata_json` stores `{type, id}` entries.
- The API also reports recent personal resources when explicit links are empty.

## Permissions

- Owner: full access, can update/delete space and manage members.
- Editor: can view and is reserved for future write capabilities.
- Viewer: can view.

The MVP exposes membership management to owners only.

## API

Add `/api/workspaces`:

- `POST /workspaces`
- `GET /workspaces`
- `GET /workspaces/{space_id}`
- `PATCH /workspaces/{space_id}`
- `DELETE /workspaces/{space_id}`
- `POST /workspaces/{space_id}/members`
- `DELETE /workspaces/{space_id}/members/{user_id}`

## Frontend

Add:

- `WorkspacePage` for list/create.
- `WorkspaceDetailPage` for overview, recent resources, members, and next actions.
- Sidebar menu entry.

## Startup Compatibility

Because the app currently enables extensions at startup but does not create every table, `init_db()` creates the new workspace tables when they do not exist. This keeps local development usable without requiring a manual migration step.

## Risks

- Metadata-based resource links are less robust than relational link tables. This is acceptable for MVP and can be migrated later.
- Current modules still primarily scope by user. Project spaces are initially an organizing layer, then can become the permission root in later P9 iterations.
