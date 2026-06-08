## Why

The Workbench can now generate proposals from user-refined gaps, but the post-generation loop is still fragmented: review signals, Copilot discussion, evolution, timeline, and board status are not presented as one coherent revision workflow. Users need a clearer path from "this proposal is weak" to "here is a revised version and exactly what changed."

## What Changes

- Add a structured proposal review package with contribution, weakness, reviewer objections, required experiments, revision plan, and writing readiness.
- Add an endpoint to create or refresh that review package for a proposal.
- Add a revision-from-review workflow that creates a child proposal using selected review guidance while preserving the parent.
- Add parent/child version comparison focused on hypothesis, approach, experiment plan, evidence, risks, and revision rationale.
- Surface review package, revision actions, and version comparison in the research project page.
- Extend proposal board status signals so proposals with review blockers or revised children are easier to triage.
- Reuse existing `evolve_idea`, lineage, timeline, and JSON metadata fields; no migration is expected.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-copilot`: add structured proposal review packages and review-guided revision actions.
- `research-idea-iteration-timeline`: add proposal version comparison and revision provenance display.
- `research-proposal-progress-board`: classify review blockers, revised proposals, and next revision actions.

## Impact

- Backend: Research Idea Workbench review helpers, Research API endpoints, proposal board classification, tests.
- Frontend: Proposal detail actions, review package panel, revision modal, comparison drawer/section, contract tests.
- Persistence: existing `ResearchIdea.review_json`, `evolution_json`, `parent_idea_id`, and `discussion_log` JSON fields.
- AI behavior: LLM is used to produce structured review and revised proposals, with deterministic fallback when unavailable.
