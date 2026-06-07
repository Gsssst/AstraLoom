## Why

The primary workflow pages still use bespoke hero cards, mixed spacing, and page-specific action placement while utility pages now share a cleaner shell. Optimizing these pages now will reduce visual drift across the core research loop without disturbing the dense workflows users already rely on.

## What Changes

- Adopt the shared `PageShell` on `PapersPage`, `ResearchPage`, `ResearchProjectPage`, and `WritingPage`.
- Replace gradient hero blocks with compact, work-focused page headers and shell actions.
- Preserve existing search, generation, writing, collection, maintenance, modal, and project workflows.
- Improve information hierarchy on primary pages by making page identity, key actions, workflow guidance, and dense work areas easier to scan.
- Add contract coverage so the primary workflow pages keep using the shared shell and do not regress to bespoke hero wrappers.

## Capabilities

### New Capabilities

### Modified Capabilities

- `shared-layout-boundaries`: Primary workflow pages should use the shared page shell while preserving their workflow-specific dense layouts.
- `paper-discovery-search-and-ingest`: Paper discovery should expose the shared shell without changing search/import behavior.
- `research-idea-workbench`: Research list and detail workbench pages should expose consistent page-level title/action structure.
- `writing-workbench-consolidation`: The writing assistant/workbench should expose consistent page-level title/action structure across assistant modes.

## Impact

- `frontend/src/pages/PapersPage.tsx`
- `frontend/src/pages/ResearchPage.tsx`
- `frontend/src/pages/ResearchProjectPage.tsx`
- `frontend/src/pages/WritingPage.tsx`
- Frontend contract tests for page shell adoption.
- OpenSpec-only requirement deltas.
- No backend API, database, dependency, or environment changes.
