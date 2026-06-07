## 1. Route Splitting

- [x] 1.1 Validate the OpenSpec change before implementation.
- [x] 1.2 Convert `App.tsx` page route imports to React lazy dynamic imports.
- [x] 1.3 Add a shared Suspense route fallback without changing route paths.

## 2. Bundle Boundaries

- [x] 2.1 Configure Vite/Rollup manual chunks for stable framework, UI, markdown, and PDF vendor groups.
- [x] 2.2 Add contract tests for lazy route imports and bundle config.

## 3. Verification

- [x] 3.1 Run OpenSpec strict validation after implementation.
- [x] 3.2 Run targeted frontend contract tests.
- [x] 3.3 Run frontend build and inspect emitted chunk split.
- [x] 3.4 Run `git diff --check`.
