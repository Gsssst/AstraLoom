## Why

The reusable workspace backlink card can collapse long project-space names into one-character vertical text in narrow sidebars, especially on research project pages. This makes linked spaces hard to read and gives the page an unstable, unfinished appearance.

## What Changes

- Update the workspace resource backlink card layout so linked and available spaces remain readable in narrow containers.
- Keep actions accessible without squeezing the workspace title column.
- Preserve the existing link/unlink behavior and API calls.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `workspace-resource-backlinks`: Backlink cards must render readable project-space names and actions in narrow resource-page containers.

## Impact

- Affects the shared `WorkspaceResourceLinks` frontend component and its styles.
- No backend API, data model, dependency, or permission changes.
