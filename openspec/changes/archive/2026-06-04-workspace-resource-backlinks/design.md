# Design: Workspace resource backlinks

## API

Add:

`GET /api/workspaces/resource-links`

Query parameters:

- `resource_type`
- `resource_id`

Response:

```json
{
  "resource_type": "papers",
  "resource_id": "...",
  "spaces": [
    {
      "id": "...",
      "name": "...",
      "role": "owner",
      "linked": true,
      "can_edit": true
    }
  ]
}
```

Only spaces visible to the current user are returned.

## Frontend

`WorkspaceResourceLinks` accepts:

- `resourceType`
- `resourceId`
- optional compact title

It displays linked spaces and available spaces, and uses existing workspace resource link/unlink endpoints.

## Scope

This iteration mounts the component on:

- Paper detail
- Research project detail
- Writing selected project panel

Bulk linking and automatic workspace suggestions are deferred.
