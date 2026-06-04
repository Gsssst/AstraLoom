# Design: Workspace resource picker

## Candidate API

Add:

`GET /api/workspaces/{space_id}/resource-candidates`

Query parameters:

- `resource_type`: `papers`, `research_projects`, or `writing_projects`
- `q`: optional search text
- `limit`: max result count

Response:

```json
{
  "items": [
    {
      "id": "...",
      "type": "papers",
      "title": "...",
      "subtitle": "...",
      "path": "/papers/...",
      "linked": false
    }
  ]
}
```

## Search Behavior

- Papers: search title/abstract/arXiv id/DOI and fall back to recent local papers when `q` is empty.
- Research projects: search current user's project name/description.
- Writing projects: search current user's writing project title/description.
- Candidates already linked to the workspace are included but marked `linked: true`.

## Frontend Behavior

- Workspace detail shows a “选择资源” control.
- User chooses resource type and search text.
- Results show title, subtitle, and linked status.
- Clicking bind calls the existing `POST /resources` endpoint.
- A compact manual id fallback remains available for unusual cases.
