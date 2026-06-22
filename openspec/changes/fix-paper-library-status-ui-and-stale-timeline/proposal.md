## Why

The local paper library reuses remote-search result status chips, so local views show irrelevant labels such as "importable" and "missing remote ID". Paper detail processing timelines can also display stale visual-evidence failure text after the current recalculated label is ready.

## What Changes

- Show remote importability status chips only for remote/search-backed result views.
- Show local paper readiness chips for local/library views instead of remote import labels.
- Ignore stale failure metadata in processing timelines when the current step label is ready.
- Add regression coverage for timeline readiness not surfacing old failure errors.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `paper-library-maintenance-center`: Local paper status displays SHALL reflect local readiness rather than remote importability.
- `paper-ingestion`: Processing timelines SHALL not show stale failure errors for currently ready processing steps.

## Impact

- Frontend paper library status strip on `PapersPage`.
- Backend processing timeline generation.
- Backend regression tests for stale failure metadata handling.
