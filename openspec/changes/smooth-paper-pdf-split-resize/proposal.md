## Why

Dragging the paper detail split between the PDF reader and AI Q&A, or expanding the desktop navigation sidebar, currently makes the PDF flash blank because each intermediate layout width forces pdf.js pages to re-render at a new width. This makes side-by-side reading feel unstable when users adjust the workspace while studying a paper.

## What Changes

- Keep the PDF visually stable while the user drags the PDF/chat split handle.
- Keep the PDF visually stable while the outer application layout is resizing, such as desktop sidebar expand/collapse.
- Defer expensive pdf.js page width recalculation until resize interactions settle.
- Preserve existing split-pane behavior, mobile panel modes, PDF page jumps, text selection, evidence highlights, and gesture zoom.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: The paper reader split workspace must avoid blank PDF re-renders during active split resizing.

## Impact

- Frontend paper detail split-pane drag handling.
- Frontend PDF viewer resize observation and react-pdf page sizing.
- Focused regression coverage for active resize behavior.
