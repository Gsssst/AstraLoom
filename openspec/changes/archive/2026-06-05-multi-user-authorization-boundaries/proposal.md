## Why

The application now supports authenticated users, but several endpoints still expose or mutate data without checking the caller's identity or resource ownership. Before adding more collaborative features, the API needs a consistent authorization boundary so one user cannot inspect or modify another user's private research workspace and ordinary users cannot invoke administrative operations.

## What Changes

- Require authentication for research workspace operations and restrict projects, ideas, experiments, and share-link creation to the owning user.
- Keep token-based shared research views public as the explicit read-only sharing path.
- Restrict folder listing, creation, nesting, and deletion to the current user's folders.
- Limit cross-user usage statistics, system dashboard data, internal task submission, and global paper-library mutations to administrators.
- Keep personal paper state isolated by the existing per-user paper records and keep public paper discovery and read-only details available.
- Add focused regression tests for user ownership filters, administrator dependencies, and protected route registration.

## Capabilities

### New Capabilities
- `multi-user-authorization`: Defines ownership checks for private resources and administrator checks for system-wide operations.

### Modified Capabilities

## Impact

- Affected backend modules: authentication dependencies, research APIs, folder APIs, usage APIs, dashboard APIs, task APIs, and global paper-library mutation routes.
- Standard users will no longer see other users' private research projects or folders and will receive `403` responses for administrator-only operations.
- Existing ownerless legacy research projects and folders are intentionally not exposed through authenticated private workspace APIs.
