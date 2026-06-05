## Why

Remote paper previews currently truncate abstracts without an expansion path, repeated searches always request the first upstream batch, and the existing backend year filters are not exposed in the paper-library interface. These gaps make discovery feel shallow even when relevant papers are available.

## What Changes

- Add a paper-summary detail modal that displays the complete available abstract and metadata from a result card.
- Pass remote search page offsets to scholarly providers so users can request a different result batch.
- Add a visible “换一批” action for remote searches.
- Add start-year and end-year filters to the paper-library search controls.
- Validate invalid year ranges before sending a request.

## Capabilities

### New Capabilities

- `paper-search-exploration-controls`: Interactive paper discovery controls for full abstract inspection, remote result pagination, and publication-year filtering.

### Modified Capabilities

None.

## Impact

- Paper-library search interface.
- Remote scholarly search orchestration and provider adapters.
- Focused backend regression tests for remote offset forwarding.

