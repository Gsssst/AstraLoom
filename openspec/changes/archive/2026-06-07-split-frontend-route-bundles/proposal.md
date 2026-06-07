## Why

The frontend production build currently emits a single app chunk above 2.5 MB, and Vite warns that chunks exceed 500 kB. Static page imports in `App.tsx` force every primary workflow page, PDF reader, chat, admin, and writing module into the initial route bundle, which slows first load and makes every feature pay for unrelated screens.

## What Changes

- Convert page-level route components to lazy-loaded dynamic imports with a shared Suspense fallback.
- Keep global providers, layout, stores, and route paths unchanged.
- Add Vite chunking configuration for stable vendor splits where it improves cacheability.
- Add contract tests that ensure page modules are no longer statically imported into `App.tsx`.
- Keep production build and TypeScript quality gates passing.

## Capabilities

### New Capabilities

- `frontend-route-bundling`: Frontend route-level code splitting and production bundle boundaries.

### Modified Capabilities

## Impact

- `frontend/src/App.tsx`
- `frontend/vite.config.ts`
- Frontend contract tests.
- No backend API, database, dependency, or environment changes.
