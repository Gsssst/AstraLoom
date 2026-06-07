## 1. Route Loader Registry

- [x] 1.1 Validate the OpenSpec change before implementation.
- [x] 1.2 Move lazy route page loaders into a shared `lazyRoutes` registry.
- [x] 1.3 Add route chunk prefetch helpers with normalized path matching and dedupe.

## 2. Intent Prefetch Adoption

- [x] 2.1 Update `App.tsx` to consume lazy route components from the shared registry.
- [x] 2.2 Add prefetch intent handlers to sidebar, mobile menu, and account/navigation actions in `AppLayout`.
- [x] 2.3 Add prefetch intent handlers to workflow step guide route actions and homepage quick actions.
- [x] 2.4 Add contract tests for route prefetch coverage and no backend API prefetching.

## 3. Verification

- [x] 3.1 Run OpenSpec strict validation after implementation.
- [x] 3.2 Run targeted frontend contract tests.
- [x] 3.3 Run frontend build.
- [x] 3.4 Run `git diff --check`.
