# Design

## Action Metadata

Workflow action items gain optional execution fields while preserving the existing shape:

- `action_type`: `"navigate"` by default, or `"api"` for executable maintenance.
- `action_label`: user-facing button label.
- `method`: HTTP method for API actions, currently `POST`.
- `endpoint`: API path relative to the frontend API base.
- `requires_admin`: marks actions that depend on existing admin-only endpoints.

This keeps current consumers compatible while allowing the frontend to render a primary "run" button for maintenance actions.

## Frontend Flow

The action center checks each item:

- For `navigate`, it keeps the current navigation behavior.
- For `api`, it calls the supplied endpoint, displays a compact result summary, refreshes action recommendations, and offers a secondary link to the detailed module page.

The existing backend permission checks remain authoritative. If a non-admin user runs an admin maintenance action, the frontend surfaces the API error.

## Maintenance Scope

This change wires only existing bounded endpoints:

- `POST /papers/maintenance/backfill-full-text?limit=5`
- `POST /papers/maintenance/backfill-embeddings?limit=20`

The limits keep the action center responsive and avoid turning a quick workflow panel into an unbounded maintenance runner.
