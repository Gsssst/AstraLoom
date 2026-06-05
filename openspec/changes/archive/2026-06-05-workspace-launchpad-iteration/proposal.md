## Why

Project spaces already support members, resource links, activities, and dashboard metrics, but they still feel like a resource list rather than the main place where a research project starts and continues. The next P9 iteration should make spaces a practical launchpad for papers, research directions, and writing work.

## What Changes

- Add clearer project-space launchpad behavior on the workspace list and detail pages.
- Add contextual quick-start actions in workspace detail for adding papers, creating research directions, and opening writing projects.
- Improve workspace cards so users can understand stage, progress, and resource coverage before opening a space.
- Keep durable resource binding and role boundaries unchanged.

## Capabilities

### New Capabilities
- `workspace-launchpad`: Project-space launchpad experience that summarizes resource coverage, exposes quick-start actions, and routes users into the right workflow module.

### Modified Capabilities
- None.

## Impact

- Frontend: workspace list/detail UI, quick action links, and contract tests.
- Backend: small deterministic fields in workspace list/detail summaries if needed.
- No database migration and no new dependency.
