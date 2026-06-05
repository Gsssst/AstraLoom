## Why

The current research-direction experience treats idea generation as a single opaque model response, so users cannot inspect the supporting literature, understand which research gap an idea addresses, compare alternatives, or refine a promising hypothesis. A useful research assistant needs an evidence-grounded, staged workflow that turns a research brief into reviewable proposals rather than a small set of disconnected idea cards.

## What Changes

- Replace the one-shot idea-generation experience with a staged Research Idea Workbench.
- Collect and classify supporting papers into seed, background, and inspiration evidence groups.
- Extract a structured Gap Map before generating hypotheses so users can inspect the limitations, conflicts, and opportunities found in the literature.
- Generate a candidate pool through multiple paths: gap-grounded hypotheses, cross-paper inspiration, and refinement of the user's own seed idea.
- Deduplicate candidates and score them with an explainable rubric covering novelty, evidence grounding, feasibility, testability, impact, and clarity.
- Persist top proposals with a falsifiable hypothesis, evidence references, review rationale, and a minimum viable experiment plan.
- Stream run stages and progress to the browser so users can see what the system is doing and inspect intermediate artifacts.
- Preserve existing project ownership boundaries and keep the existing discussion and code-generation actions available for selected proposals.

## Capabilities

### New Capabilities

- `research-idea-workbench`: Evidence-grounded research brief processing, Gap Map extraction, multi-path candidate generation, deduplication, explainable review, proposal persistence, and visible run progress.

### Modified Capabilities

None.

## Impact

- Adds a new persisted idea-run model and richer structured metadata for research ideas.
- Adds workbench run, progress-stream, and run-detail API endpoints under the existing research project API.
- Introduces an independent workbench service rather than extending the legacy one-shot idea-generation algorithm.
- Reworks the research project detail page into a staged workbench while retaining existing project, discussion, and code-generation flows.
- Adds backend tests for staged runs, ownership checks, artifact persistence, candidate ranking, and compatibility behavior.
