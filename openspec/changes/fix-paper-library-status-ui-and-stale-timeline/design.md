## Context

`PapersPage` has one result-status strip shared by local and remote sources. The strip is useful for remote search/import workflows but misleading for local paper library views where every item is already local and remote IDs are not the user's concern.

`paper_processing_snapshot()` recalculates current labels from present artifacts, but `_processing_timeline_from_labels()` still attaches `failed_steps` metadata to a label even when that label is now ready. This can show an old visual OCR failure under a green ready card.

## Goals / Non-Goals

**Goals:**

- Keep remote-search status chips for import workflows.
- Use local readiness chips for local/library views.
- Suppress old failure text/timestamps for labels whose current state is ready.

**Non-Goals:**

- Redesign the whole paper library filter panel.
- Delete historical failure metadata from the database.
- Change paper processing orchestration behavior.

## Decisions

- Render different status strips based on `isSearchBackedSource`.
  - Remote/search-backed views keep importability chips.
  - Local views show total, full text, vector, visual evidence, and open PDF counts.

- Filter timeline failure metadata at render-model generation time.
  - If the current label state is `ready`, stale `failed_steps[label.key]` SHALL not provide error, failed_at, or retry hint.
  - This avoids destructive metadata cleanup while making the UI reflect current truth.

## Risks / Trade-offs

- Local status counts are page/list scoped, not global database totals.
  - Mitigation: keep the existing "结果状态" label and count from currently loaded `papers`.

- Historical failure metadata remains in `metadata_json`.
  - Mitigation: it is still available for diagnostics, but it no longer overrides ready timeline display.
