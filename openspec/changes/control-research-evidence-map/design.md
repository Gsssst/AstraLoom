## Context

Recent proposal quality improvements tightened selected ideas, but evidence selection remains mostly automatic. Comparable systems suggest that evidence should be inspectable and steerable:

- PaperQA-style systems expose answer evidence and citations, so users can inspect which sources support a claim.
- STORM-style systems make retrieval and outline construction visible before writing.
- OpenScholar/OpenResearcher-style research agents treat search, filtering, and source grounding as first-class steps rather than hidden context.

For this product, the pragmatic next step is not a new retrieval engine. It is to make the existing Evidence Map configurable before Gap Map and Proposal generation.

## Goals

- Let users control how many evidence papers enter generation.
- Let users pin papers that must remain in the Evidence Map.
- Let users exclude papers that should not influence ideas.
- Preserve the current one-click default flow.
- Store evidence controls on the run for reproducibility.

## Non-Goals

- Do not replace the existing retrieval/ranking implementation.
- Do not add a new database table.
- Do not build a full graph visualization.
- Do not require external search providers to be available.

## Backend Design

Add a normalized `evidence_controls` object:

```json
{
  "max_items": 12,
  "pinned_paper_ids": ["..."],
  "excluded_paper_ids": ["..."]
}
```

Normalization:

- `max_items` clamped to 3-30.
- pinned/excluded IDs are unique strings.
- excluded wins over pinned if the same ID appears in both.

Filtering:

- Apply controls after `collect_evidence` returns an Evidence Map.
- Preserve category order: `seed`, `background`, `inspiration`.
- Pinned items are retained first when available.
- Excluded items are removed from every category.
- Remaining items fill up to `max_items`.
- Add `controls` and `control_summary` to the stored Evidence Map.

API:

- Extend `GenerateIdeasRequest` and Gap Preview request with optional evidence controls.
- Extend continue-from-gaps request with optional evidence controls so users can refine Evidence Map after preview.
- During continuation, reapply controls to the stored evidence map before generation.

## Frontend Design

On the Evidence Map tab:

- Add a small control bar:
  - evidence count select/stepper
  - pinned count
  - excluded count
  - buttons to clear pins/exclusions
- On each evidence item:
  - `固定` toggle
  - `排除` toggle
- Gap Map preview and generation continuation send the controls.
- Display active control summary when a run has controls.

The UI should remain dense and work-focused; avoid adding a large new wizard.

## Testing

- Backend:
  - normalize controls
  - apply controls with pinned/excluded/max item behavior
  - preview run persists controls and filtered Evidence Map
- Frontend contract:
  - state for evidence controls exists
  - preview/continue requests include evidence controls
  - Evidence Map tab exposes pin/exclude controls
- Verification:
  - focused pytest
  - frontend contract test
  - OpenSpec strict validation
  - frontend build
