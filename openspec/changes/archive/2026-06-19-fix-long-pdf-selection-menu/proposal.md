## Why

Selecting a longer passage in the PDF reader currently fails to show the contextual action menu, so users cannot ask, explain, copy, save, or add notes from longer paper excerpts. This blocks a common reading workflow: selecting a full abstract paragraph or multi-line method description.

## What Changes

- Allow longer PDF text selections to trigger the existing contextual action menu.
- Anchor the selection menu using a stable visible selection rectangle when a range spans many lines.
- Preserve existing compact menu actions and do not auto-insert selected text into the question composer.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-reader-grounded-interaction`: PDF contextual selection actions remain available for longer multi-line selections.

## Impact

- Frontend: update PDF text selection handling and paper detail selection menu positioning.
- Tests: extend paper selection action contract coverage.
