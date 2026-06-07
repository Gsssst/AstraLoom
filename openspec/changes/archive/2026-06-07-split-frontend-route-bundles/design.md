## Context

`frontend/src/App.tsx` statically imports every page module. Heavy screens such as chat, paper detail/PDF reading, papers, research workbench, writing, and admin all land in the initial app chunk even when the user opens a simple route. The production build currently emits a main JavaScript asset above 2.5 MB and Vite reports the standard 500 kB chunk warning.

Reference scan:
- React official documentation recommends `lazy` and `Suspense` to defer component code loading until it is first rendered.
- React Router supports route elements backed by dynamically imported components.
- Vite recommends dynamic imports and Rollup `manualChunks` when large chunks should be split or cached separately.

## Goals / Non-Goals

**Goals:**
- Split page modules into route-level dynamic imports.
- Keep global providers, AppLayout, auth fetch behavior, theme behavior, and route paths unchanged.
- Provide a small, shared fallback while a lazy route chunk is loading.
- Add Vite vendor chunk boundaries for stable high-volume dependencies.
- Add contract tests for lazy page imports and bundle configuration.

**Non-Goals:**
- Change routing semantics or URLs.
- Add a new routing library or bundling plugin.
- Rewrite page internals for fine-grained component-level splitting.
- Guarantee every emitted asset is below 500 kB; some vendor chunks such as PDF workers may legitimately remain large.

## Decisions

- Use `React.lazy` for page modules in `App.tsx`.
  - Rationale: It is the smallest change that removes page code from the initial route bundle while preserving the existing `<Routes>` tree.
  - Alternative considered: React Router data router `lazy`; rejected because it would require a larger router refactor without much benefit for this iteration.

- Wrap route elements with one reusable Suspense fallback.
  - Rationale: Users should see a consistent lightweight loading state when switching to a route whose chunk has not loaded.
  - Alternative considered: per-page fallback copy; rejected for this first bundle-splitting pass because fallback duration is expected to be short.

- Add `manualChunks` for stable vendor groups.
  - Rationale: Ant Design, React, Markdown/KaTeX, and PDF-related code have different cache and usage profiles.
  - Alternative considered: rely only on dynamic imports; accepted for page code but not enough to improve vendor cache boundaries.

## Risks / Trade-offs

- [Risk] Lazy routes introduce an extra network request when navigating to a page for the first time.
  -> Mitigation: keep fallback small and split at page level only.
- [Risk] Manual chunk names can become stale if dependencies change.
  -> Mitigation: keep groups broad and test that the config contains the expected boundaries.
- [Risk] Build output can still warn for inherently large vendor assets.
  -> Mitigation: measure before/after and focus on reducing the initial app chunk, not hiding warnings by only raising the limit.
