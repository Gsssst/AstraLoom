## Why

Route-level lazy loading reduced the initial app chunk, but the first navigation to a page can still show the route fallback while the chunk downloads. High-intent navigation surfaces such as the sidebar, mobile drawer, homepage quick actions, and workflow step guides can prefetch the target route chunk before the user clicks.

## What Changes

- Add a route prefetch registry that maps known app routes to the same dynamic imports used by lazy route components.
- Trigger route chunk prefetch on navigation intent, such as hover/focus/touch start on sidebar items and workflow guide actions.
- Keep route prefetch limited to JavaScript chunk loading; do not prefetch page data or call backend APIs.
- Add contract tests that ensure route prefetch coverage stays aligned with lazy route registration and navigation surfaces.

## Capabilities

### New Capabilities

### Modified Capabilities

- `frontend-route-bundling`: Extend lazy route bundling with route chunk prefetch on user navigation intent.

## Impact

- `frontend/src/routes/lazyRoutes.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/AppLayout.tsx`
- `frontend/src/components/WorkflowStepGuide.tsx`
- `frontend/src/pages/HomePage.tsx`
- Frontend contract tests.
- No backend API, database, dependency, or environment changes.
