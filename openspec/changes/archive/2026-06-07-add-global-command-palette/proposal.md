## Why

The app now has several polished workflow pages, but users still need to manually move through sidebar navigation, page-specific search boxes, and separate action buttons to resume common work. A global command palette gives power users one keyboard-first entry point for navigation, resource lookup, and frequent actions.

## What Changes

- Add a global command palette that opens from `Ctrl/⌘ + K` and an explicit header trigger.
- Show grouped commands for primary routes, common workflow actions, and lightweight resource search results.
- Let users jump to papers, research projects, workspaces, writing tools, settings, and digest/action-center pages from one surface.
- Reuse existing frontend APIs for resource search and listing; do not add a new backend endpoint or dependency in this change.
- Preserve existing page routes, sidebar navigation, and route chunk prefetch behavior.

## Capabilities

### New Capabilities
- `global-command-palette`: Defines the keyboard-first command palette, grouped navigation/actions, resource search behavior, and responsive interaction contract.

### Modified Capabilities

## Impact

- `frontend/src/components/GlobalCommandPalette.tsx`
- `frontend/src/components/AppLayout.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles/responsive.css`
- Frontend contract tests.
- No backend API, database, dependency, or environment changes.
