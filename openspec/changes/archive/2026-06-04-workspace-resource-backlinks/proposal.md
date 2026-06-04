# Change: Workspace resource backlinks

## Why

Users can now attach resources from a workspace page, but resource pages still do not show which workspaces they belong to. This makes the workflow one-directional: users must start from the workspace to manage associations. Resource pages should expose their workspace memberships and allow direct join/remove actions.

## What Changes

- Add a workspace resource link status endpoint for any supported resource.
- Return the current user's visible spaces with linked status and role.
- Add a reusable frontend resource-workspace link component.
- Mount the component on paper detail, research project, and writing project pages.

## Impact

- Existing link/unlink resource APIs are reused.
- No resource ownership changes.
- Resource pages gain direct workspace association controls.
