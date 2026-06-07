## Why

The Workbench now lets users preview and select Gap Map items, but users still cannot correct weak gaps, mark why a gap is unsuitable, or refine one gap without rerunning the full pipeline. This leaves proposal generation dependent on the first extracted Gap Map even when the user can spot quality issues immediately.

## What Changes

- Add editable Gap Map feedback metadata for each gap: edited text fields, quality rating, feedback labels, user notes, and evidence rationale visibility.
- Add an owner-scoped API to update Gap Map feedback on a reviewed run without creating proposals.
- Add an owner-scoped API to refine a single Gap Map item using its evidence, current text, and user feedback.
- Feed edited gaps, labels, ratings, and user notes into the continue-from-gaps generation context.
- Persist Gap feedback in existing run JSON artifacts and final run review metadata.
- Add frontend controls for editing a gap, rating/labeling it, viewing linked evidence, and refining one gap.
- Keep the existing one-click generation and current Gap selection flow working without requiring feedback.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-workbench`: add Gap Map feedback, per-gap editing, evidence rationale inspection, and single-gap refinement before proposal generation.
- `research-idea-generation-v3`: require candidate generation and evolution to respect edited Gap Map feedback and quality labels.

## Impact

- Backend: Research Idea Workbench service, project run APIs, and tests around Gap Map metadata mutation.
- Frontend: Research project Gap Map tab controls, applied feedback display, and contract tests.
- Persistence: no migration expected; feedback lives in existing `ResearchIdeaRun.gap_map`, `config_json`, and `review_summary` JSON fields.
- AI behavior: prompts for candidate generation and gap refinement include user feedback as guidance, with deterministic fallback when model output is unavailable.
