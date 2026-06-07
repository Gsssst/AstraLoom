## 1. Route Loader Registry

- [ ] 1.1 Validate the OpenSpec change before implementation.
- [ ] 1.2 Move lazy route page loaders into a shared `lazyRoutes` registry.
- [ ] 1.3 Add route chunk prefetch helpers with normalized path matching and dedupe.

## 2. Intent Prefetch Adoption

- [ ] 2.1 Update `App.tsx` to consume lazy route components from the shared registry.
- [ ] 2.2 Add prefetch intent handlers to sidebar, mobile menu, and account/navigation actions in `AppLayout`.
- [ ] 2.3 Add prefetch intent handlers to workflow step guide route actions and homepage quick actions.
- [ ] 2.4 Add contract tests for route prefetch coverage and no backend API prefetching.

## 3. Verification

- [ ] 3.1 Run OpenSpec strict validation after implementation.
- [ ] 3.2 Run targeted frontend contract tests.
- [ ] 3.3 Run frontend build.
- [ ] 3.4 Run `git diff --check`.
