## Why

The paper library can mark papers as shared "important" or "interesting", but users cannot retrieve those groups from the library search controls. This makes the markers useful on individual cards but weak for resurfacing important reading sets.

## What Changes

- Add an `importance_label` filter to local paper search.
- Apply the filter consistently when browsing and keyword-searching local papers.
- Add a paper library filter control for all, important, and interesting papers.
- Add focused backend and frontend contract coverage.

## Capabilities

### Modified Capabilities
- `paper-search`: Users can filter local paper library results by shared importance marker.

## Impact

- Backend paper search API query parameters and filtering.
- Paper library frontend filter toolbar.
- Paper search OpenSpec requirements and contract tests.
