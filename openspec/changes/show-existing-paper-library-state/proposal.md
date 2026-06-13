## Why

Remote paper search and digest/push surfaces can show papers that already exist in the local paper library. Users currently still see an active "加入论文库" action, so they cannot tell whether clicking will import a new paper or hit an existing record.

## What Changes

- Detect local-library matches for remote paper previews using stable identifiers and normalized titles.
- Return existing-library state in remote search/digest preview payloads.
- Disable the add-to-library action for papers already in the local library.
- Show the action as "已在论文库" with a stable visual state instead of an import button.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `external-paper-ingest-transparency`: remote paper cards SHALL show when a result is already in the local paper library and disable ingest.

## Impact

- Backend paper search/digest preview response fields and duplicate matching helper.
- Paper library search result UI and digest/push paper cards that reuse remote preview data.
- Tests covering duplicate-state payloads and disabled import actions.
