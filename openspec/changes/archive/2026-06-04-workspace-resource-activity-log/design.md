# Design: Workspace resource binding and activity log

## Model

Add two workspace-owned tables:

- `project_space_resources`
  - `space_id`
  - `resource_type`: `paper`, `research_project`, or `writing_project`
  - `resource_id`: stored as string to support mixed UUID/string ids already present in the app
  - `added_by`
  - `metadata_json`

- `project_space_activities`
  - `space_id`
  - `actor_id`
  - `action`
  - `resource_type`
  - `resource_id`
  - `metadata_json`

Resource links are unique by `(space_id, resource_type, resource_id)`.

## Permissions

- Owners and editors can link/unlink resources.
- Viewers can inspect linked resources and activity.
- Owners manage members and delete/update spaces.
- Admin console can inspect recent activity but not mutate it through this change.

## Compatibility

Existing `metadata_json.resource_links` entries are included in summaries as legacy links. New links are written to `project_space_resources`.

## Frontend

The workspace detail page gains:

- A resource attachment panel with resource type and id.
- Linked resources sourced from durable links.
- A recent activity timeline explaining who did what.

The admin page gains a recent workspace activity card.
