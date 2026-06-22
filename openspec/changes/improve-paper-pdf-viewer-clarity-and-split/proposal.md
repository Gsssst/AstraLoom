## Why

The paper PDF reader currently renders each page at the fit-to-panel width and then enlarges that rendered canvas with a CSS transform. At higher zoom levels this scales pixels instead of re-rendering the page, so formulas and small text look blurry compared with arXiv or browser-native PDF viewers.

The PDF/chat split also keeps the PDF panel at a minimum of 42%, which prevents users from making the AI Q&A panel wide enough for longer grounded answers.

## What Changes

- Render `react-pdf` pages at the effective zoomed width instead of scaling a lower-resolution canvas with CSS transforms.
- Increase toolbar and modifier-wheel zoom sensitivity so touchpad/Ctrl-wheel zoom feels closer to a normal PDF viewer.
- Allow the paper AI Q&A panel to be resized wider by reducing the PDF panel minimum width while preserving the existing collapsed chat rail behavior.
- Update frontend contract tests to lock in high-resolution PDF zoom and the wider split range.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The PDF reader provides clear high-zoom rendering and a wider adjustable PDF/chat split.

## Impact

- Frontend PDF viewer rendering and zoom behavior.
- Paper detail split resize constraints.
- PDF reader responsive styles.
- Frontend contract tests for PDF zoom and split resizing.
