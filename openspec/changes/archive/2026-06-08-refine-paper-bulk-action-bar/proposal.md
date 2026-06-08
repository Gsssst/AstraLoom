## Why

The selected-paper bulk action bar can visually overlap when several action groups are visible, especially after adding report presets and library maintenance actions around the same workflow. This makes common paper-library operations look crowded and harder to scan.

## What Changes

- Refine the selected-paper bulk action bar into a cleaner grouped toolbar.
- Ensure action groups wrap with stable spacing instead of overlapping.
- Keep existing collection, reading-status, export, report, tagging, and clear-selection actions.
- Preserve responsive behavior on narrow screens.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-bulk-actions-export`: The selected-paper bulk action bar layout requirement is tightened to require non-overlapping grouped controls across available widths.

## Impact

- Frontend: `PapersPage.tsx`, responsive toolbar CSS, and frontend contract tests.
- Backend/API: none.
