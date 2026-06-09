## Why

Toolbox entries are currently passed into idea generation as raw prompt context. That makes selected tools visible to the model, but it does not explicitly decide which tool fits which gap, whether a tool should be a contribution, baseline, dataset, metric, or something to avoid, or why a generated proposal used it.

## What Changes

- Add a deterministic `tool_fit_plan` stage inside the Research Idea Workbench generation context.
- Score selected toolbox entries against the current Gap Map and project brief before candidate generation.
- Assign each selected tool a role-aware use plan based on tool kind and user-selected tool mode.
- Feed the compact `tool_fit_plan` into candidate generation, candidate evolution, fallback candidates, review summary, and persisted proposal metadata.
- Surface selected proposal tool-fit rationale in the research project UI without adding a new page.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `research-idea-workbench`: Idea generation should use a structured toolbox fit plan rather than only raw selected toolbox context.

## Impact

- Backend Research Idea Workbench service: generation context assembly, prompt construction, fallback candidates, review summary, persisted proposal metadata.
- Frontend research project page: proposal detail display for tool-fit rationale.
- Tests: backend helper tests for tool-fit planning and frontend contract tests for display/payload wiring.
