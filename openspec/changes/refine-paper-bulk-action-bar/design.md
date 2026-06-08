## Context

The bulk action bar is fixed near the bottom of the paper library and currently renders each action group in a single horizontal run. On medium desktop widths, labels and buttons can compete for space and visually overlap.

## Goals / Non-Goals

**Goals:**
- Make the selected-paper toolbar scan cleanly at desktop and narrow widths.
- Give each action group stable spacing and wrapping behavior.
- Keep the current action surface and handlers unchanged.

**Non-Goals:**
- Redesign bulk action behavior or add new actions.
- Change backend endpoints or export formats.

## Decisions

- Use a flex toolbar with grouped "pill" sections and `flex-wrap`.
- Give the count area a fixed minimum width and each action group a bounded min width.
- Keep labels small and uppercase-like through CSS, while buttons remain standard Ant Design controls.
- On narrow screens, allow groups to become full-width rows so text never overlaps.

## Risks / Trade-offs

- The toolbar may become taller when many actions are available. This is acceptable because a taller non-overlapping toolbar is easier to use than a compressed single row.
- The bottom fixed toolbar still consumes vertical space while visible. Existing clear-selection behavior remains available.
