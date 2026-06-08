## Why

Research proposals currently expose many signals, but users still need to decide manually whether to gather evidence, discuss with AI, validate novelty, design experiments, generate code, or move into writing. PDF text selection also works, but the browser selection overlay appears too heavy and visually merges adjacent lines.

## What Changes

- Add an idea-level next-action panel that turns proposal state into clear workflow actions.
- Surface actions such as AI discussion, timeline review, validation, experiment feedback, code project generation, writing handoff, and evidence review from each proposal.
- Refine PDF reader selection/highlight styling so selected text is lighter, line-separated, and easier to read.
- Add frontend contract tests for the next-action panel and selection styling.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `research-idea-workbench`: Proposal cards expose an actionable next-step panel.
- `paper-reader-grounded-interaction`: PDF text selection uses a readable, non-blocky highlight treatment.

## Impact

- Frontend research project page UI and local action routing.
- Frontend PDF reader styles.
- Frontend contract tests.
- No database, backend API, or model-call behavior changes.
