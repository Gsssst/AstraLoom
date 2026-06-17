## Why

The paper detail PDF pane can render dense academic PDFs at a small size, especially when the chat panel is open. Users need a quick way to inspect small text, table values, and figure labels without changing page layout or losing their reading position.

## What Changes

- Add a toggleable local magnifier to the enhanced PDF reader.
- Show a bounded loupe near the cursor while the magnifier is active and the pointer is over a rendered PDF page.
- Keep existing scrolling, page tracking, text selection, and evidence jump behavior unchanged.
- Hide the magnifier in native PDF fallback mode where the app does not control the PDF rendering layer.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: The PDF reader supports local magnification for rendered PDF pages without disrupting reading or selection workflows.

## Impact

- Frontend PDF viewer component and responsive styles.
- Frontend contract tests for the magnifier control and CSS hooks.
