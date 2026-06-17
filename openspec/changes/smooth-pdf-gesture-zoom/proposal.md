## Why

The global PDF zoom currently changes the `react-pdf` page render width on every wheel or pinch event. That forces pdf.js to repaint canvases repeatedly, causing white flashes before the page becomes larger and making zoom feel unlike mature PDF viewers.

## What Changes

- Keep rendered PDF pages stable during interactive zoom gestures.
- Apply visual zoom through a CSS transform and reserve the scaled layout size around each page.
- Keep toolbar and Ctrl/Cmd-wheel or touchpad pinch controls from the previous global zoom change.
- Preserve evidence highlighting, text selection, and page navigation after zoom.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-reader-grounded-interaction`: The PDF reader zoom interaction must not blank or visibly re-render pages on every gesture step.

## Impact

- Frontend PDF viewer component.
- Responsive PDF layout styles.
- Frontend zoom contract tests.
