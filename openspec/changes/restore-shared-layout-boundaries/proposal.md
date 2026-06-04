## Why

The refreshed application shell removed shared layout class names that high-traffic workspaces still rely on for content spacing and responsive behavior. The chat workspace consequently applies its intentional negative fill margin against an unpadded container and overlaps the global header at the top-left and top-right edges.

## What Changes

- Restore the shared application shell class contract on the main layout, header, and content containers.
- Preserve the refreshed sidebar, logo, account, and chat visual styling.
- Add a focused regression check for the shared class contract.

## Capabilities

### New Capabilities
- `shared-layout-boundaries`: Keep page workspaces contained below the global header while preserving responsive spacing rules.

### Modified Capabilities

## Impact

- Shared frontend shell: `frontend/src/components/AppLayout.tsx`
- Frontend regression checks for shell class names and workspace containment

