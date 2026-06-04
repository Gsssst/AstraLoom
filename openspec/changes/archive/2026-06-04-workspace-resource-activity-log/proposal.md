# Change: Workspace resource binding and activity log

## Why

Project spaces currently summarize recent owner resources and read legacy `metadata_json.resource_links`, which makes workspace ownership hard to reason about. Users need a clearer way to attach papers, research projects, and writing drafts to a space, and admins need activity visibility for governance.

## What Changes

- Add durable workspace resource links for papers, research projects, and writing projects.
- Add workspace activity records for creation, member changes, resource linking, resource unlinking, and workspace updates.
- Expose workspace activity in the workspace detail page.
- Expose recent workspace activity in the admin console.

## Impact

- New database tables for `project_space_resources` and `project_space_activities`.
- Workspace detail APIs return durable resource links and activity timeline.
- Existing legacy `metadata_json.resource_links` remains readable for compatibility.
