# Change: Workspace resource access control

## Why

Project spaces can now bind resources, but linked research projects and writing drafts still behave mostly as owner-only resources. This creates a mismatch: a workspace member can see that a resource belongs to the workspace, but may fail when opening or collaborating on it. Workspace membership should grant practical access to linked resources.

## What Changes

- Add service-level workspace resource role lookup.
- Allow workspace viewers to read linked research projects and writing drafts.
- Allow workspace owners/editors to update linked research projects and writing drafts.
- Keep destructive deletion owner-only for this iteration.
- Surface access metadata in returned writing projects where practical.

## Impact

- Research and writing APIs gain workspace-aware access checks.
- Existing owner-only behavior remains valid.
- Workspace-linked collaboration becomes usable without duplicating resources.
