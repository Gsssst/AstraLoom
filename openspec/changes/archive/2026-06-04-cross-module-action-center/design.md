# Design: Cross-module action center

## Approach

The first version is a generated action center rather than a stored task system. It reads existing project state and returns a compact list of action recommendations:

- Paper maintenance: low full-text or embedding coverage, unread saved papers.
- Digest workflow: unread or pending digest notifications.
- Research workflow: active research projects and draft ideas.
- Writing workflow: draft writing projects.
- Workspace workflow: active project spaces and their next-action suggestions.

Each action includes `id`, `group`, `priority`, `title`, `description`, `path`, `source`, and optional metadata. The frontend groups cards by workflow area and lets users jump to the relevant module.

## Rationale

This keeps the feature balanced across existing modules and avoids over-investing in a single part of the product. A generated action surface is also safer than adding a new persistent task model before we know how users want to manage tasks.

## API Shape

`GET /api/workflow/actions`

Returns:

```json
{
  "summary": {
    "total": 8,
    "high_priority": 2,
    "groups": {"papers": 3, "research": 2, "writing": 1, "workspaces": 2}
  },
  "actions": [
    {
      "id": "papers:full-text",
      "group": "papers",
      "priority": "high",
      "title": "补全文覆盖",
      "description": "当前全文覆盖率偏低，建议先补全文再做论文问答。",
      "path": "/settings",
      "source": "knowledge-maintenance"
    }
  ]
}
```

## Frontend

Add `/actions` under `AppLayout`. The page uses summary cards and grouped action lists. It is intentionally not editable yet; each action routes to the module where work is performed.

## Risks

- Recommendations may feel generic if they only count records. Mitigation: include concrete titles for recent unread papers/projects/drafts.
- Too many actions could overwhelm users. Mitigation: cap each group and sort by priority.
