## Why

The paper reader currently collapses the AI panel only after a very narrow drag range, and the PDF remains capped at a fixed percentage after collapse, leaving unused whitespace. The opposite workflow is missing entirely: users cannot drag the PDF away to give the AI answer the full workspace.

## What Changes

- Add bidirectional snap thresholds to the desktop PDF/AI split handle.
- Collapse AI Q&A into its existing narrow rail when the divider is dragged far enough right, while allowing the PDF reader to fill all remaining width.
- Collapse the PDF reader into a narrow rail when the divider is dragged far enough left, while allowing AI Q&A to fill all remaining width.
- Provide explicit rail buttons for restoring either collapsed panel to the default split.
- Preserve PDF resize pausing, mobile panel switching, chat history, and evidence navigation.
- Add regression coverage for both collapse directions and full-width fill behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: The desktop paper reading split gains bidirectional threshold-based panel collapse and restoration.

## Impact

- Frontend paper detail split state and pointer resize handlers.
- Paper detail collapsed rail styles.
- Focused frontend contract tests.
- No backend API or data migration changes.
