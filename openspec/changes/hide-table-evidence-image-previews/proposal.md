## Why

Paper Q&A table evidence currently renders as visual preview cards when an asset path exists. Table crops often look like broken or tiny unreadable images in the answer panel, causing visual clutter while the citation chips already provide the useful page navigation and evidence labels.

The answer citation area also expands every reference by default, which consumes too much chat space for evidence-heavy method and experiment answers. In the paper library maintenance center, the top-level batch buttons also show both the old structured PDF parse action and the current visual evidence extraction action, making it unclear which path is the current multimodal pipeline.

## What Changes

- Stop rendering image preview cards for table-like evidence references.
- Keep non-table visual evidence previews for figures, charts, diagrams, and architecture evidence.
- Collapse paper Q&A references by default behind a compact evidence summary, with click-to-expand details.
- Continue showing table evidence as citation chips with page navigation and tooltips when the user expands references.
- Remove the prominent top-level "解析 5 篇 PDF" maintenance action while keeping the current "提取 5 篇视觉证据" batch action.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `visual-evidence-crops`: Preview cards should be limited to non-table visual evidence; table evidence should remain compact textual/page-navigation references.
- `paper-library-maintenance-center`: Top-level repair actions should promote the current visual evidence extraction path and avoid exposing the old structured PDF parse batch action as a peer primary action.

## Impact

- Frontend: paper detail chat evidence rendering, paper library maintenance action row, and contract tests.
- Backend/API: no change.
