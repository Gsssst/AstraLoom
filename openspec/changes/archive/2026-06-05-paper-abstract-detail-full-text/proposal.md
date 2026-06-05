## Why

The new paper-summary modal still displays truncated text because the search-card response only exposes the 500-character preview field. Users need the complete available abstract when evaluating a remote result before ingestion.

## What Changes

- Preserve the existing short card-preview abstract.
- Add a dedicated full-abstract response field for paper-card detail views.
- Render the full-abstract field inside the paper-summary modal with a preview fallback for compatibility.

## Capabilities

### New Capabilities

- `paper-abstract-detail-full-text`: Complete available abstract text in paper-card detail views while retaining concise list previews.

### Modified Capabilities

None.

## Impact

- Paper brief API response model and mapper.
- Paper-library abstract modal.
- Focused API regression test.

