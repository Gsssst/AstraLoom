## Why

High-resolution PDF zoom now renders pages at the active zoom width, which fixes blurry formulas and text. However, continuous pinch/Ctrl-wheel zoom can trigger repeated `react-pdf` canvas re-renders, causing pages to briefly flash white while the new canvas is painted.

Users expect zoom to feel continuous like a normal PDF viewer: the page should visually scale immediately during the gesture, then settle into a crisp rendered version once the gesture pauses.

## What Changes

- Add two-stage PDF zoom rendering:
  - `displayZoomScale` updates immediately for toolbar and gesture feedback.
  - `renderZoomScale` updates after a short idle delay so `react-pdf` re-renders once the gesture settles.
- Use CSS transform only as a transient preview when display zoom differs from the last rendered zoom.
- Keep the final settled PDF canvas/text/annotation layers rendered at the active zoom width.
- Update contract tests to prevent regressions to either blurry CSS-only zoom or flash-prone per-wheel re-rendering.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: PDF zoom remains clear after settling and avoids white flashes during continuous zoom gestures.

## Impact

- Frontend PDF viewer zoom state and rendering behavior.
- PDF reader zoom contract tests.
