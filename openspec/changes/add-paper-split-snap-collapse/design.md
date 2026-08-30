## Context

`PaperDetailPage` already owns the desktop PDF/chat split width, pauses PDF page resizing during pointer drags, and can replace AI Q&A with a narrow rail. The current AI collapse leaves the PDF at a fixed `82%`, so the remaining workspace is not consumed. There is no equivalent PDF rail when users want a wide AI workspace.

## Goals / Non-Goals

**Goals:**

- Make the existing divider snap to a collapsed AI rail near the right edge.
- Add the symmetric PDF rail near the left edge.
- Let the non-collapsed panel flex into all space not occupied by the rail and divider.
- Restore either side to the normal 65/35 split with one click.
- Preserve active-resize signaling to `PDFViewer`.

**Non-Goals:**

- Persisting split or collapsed state across page reloads.
- Changing mobile panel tabs.
- Changing PDF rendering, paper chat retrieval, or backend APIs.

## Decisions

- Keep explicit `chatCollapsed` and add `pdfCollapsed`.
  - Rationale: this is the smallest change compatible with existing tests and rail rendering.
  - Alternative: replace both with a single enum. That is cleaner in isolation but creates wider churn in a large page component.
- Evaluate raw pointer percentage before applying normal min/max clamping.
  - Rationale: the pointer can cross a collapse threshold even though the visible expanded panels retain usable minimum widths.
- Use mutually exclusive state transitions.
  - Rationale: entering either collapse threshold always clears the opposite collapsed state, preventing an impossible double-collapse layout.
- Keep the divider rendered beside either rail.
  - Rationale: users can drag back out of a collapsed state as well as click the rail restore button.
- Use flex fill only in collapsed layouts.
  - Rationale: normal split widths remain deterministic, while the expanded side consumes all remaining width after collapse.

## Risks / Trade-offs

- [Risk] Rapid threshold crossing could cause visual jitter. → Use separated collapse thresholds and restore to the normal split on rail click.
- [Risk] PDF canvas width can briefly differ during drag. → Preserve the existing `pdfSplitResizing` pause and final measurement behavior.
- [Risk] A narrow viewport may make rails crowded. → Limit the new behavior to the existing desktop split path; mobile continues using tabs.
