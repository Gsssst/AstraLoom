## Why

The paper library currently supports personal saves and reading states, but there is no library-wide way to signal that a paper is important or especially interesting. Teams need a visible shared marker so high-value papers stand out for everyone.

## What Changes

- Add a global paper importance marker stored on the paper record.
- Support two visible labels: important and interesting.
- Allow signed-in users to set or clear the shared marker and optional short note.
- Show the marker in paper search/list results and paper detail.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-api`: Paper records expose and update shared importance markers.
- `paper-search`: Search/list responses include shared importance marker metadata.
- `paper-annotation-and-reading-loop`: Paper detail shows and lets users maintain shared importance markers alongside personal reading state.

## Impact

- Database migration for paper-level marker fields.
- Paper ORM and API response models.
- Paper list/detail frontend display and actions.
- Backend tests for marker persistence and response serialization.
