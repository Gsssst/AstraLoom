## Context

The product already has several pieces of a proposal iteration workflow: saved proposals, validation, adversarial review metadata, Copilot discussion, discussion-driven evolution, experiment-feedback evolution, lineage, timeline, and a project progress board. The problem is that those pieces are not integrated into a clear revision loop. Users can ask questions or evolve a proposal, but they do not get a structured reviewer package, a revision plan, or a concise version comparison.

Open-source research ideation systems point toward making critique and revision explicit:
- Open Coscientist-style flows separate hypothesis generation, review, ranking, and evolution.
- Open AI Co-Scientist implementations expose reflection, ranking, proximity checks, and evolution stages.
- Research proposal writing tools often distinguish reviewer comments, revision plan, and response/revision rationale.

This change connects existing project pieces into a Proposal-level review and revision loop while keeping persistence in current JSON fields.

## Goals / Non-Goals

**Goals:**
- Generate and persist a structured review package for each proposal.
- Let users create a revised child proposal directly from review guidance.
- Show parent/child version differences in hypothesis, approach, experiment, risks, evidence, and rationale.
- Surface review blockers and revised status in the proposal board.
- Reuse existing evolution, lineage, timeline, and JSON persistence patterns.

**Non-Goals:**
- New relational version tables.
- Multi-reviewer collaborative review assignments.
- Full paper manuscript diffing.
- Replacing Copilot chat or validation; this change packages their signals into a revision workflow.

## Decisions

### Store review package under `review_json.proposal_review`

The proposal review package will live in `ResearchIdea.review_json.proposal_review` and include:
- `summary`
- `contributions`
- `weakest_assumptions`
- `reviewer_objections`
- `required_experiments`
- `revision_plan`
- `writing_readiness`
- `next_revision_focus`

This keeps the review package attached to the proposal and avoids a migration.

### Add explicit review and revise endpoints

Two APIs will make the workflow discoverable:
- `POST /api/research/ideas/{idea_id}/review-package`
- `POST /api/research/ideas/{idea_id}/revise-from-review`

The first refreshes the structured review package. The second calls the existing `evolve_idea` path using selected review guidance and annotates the child `evolution_json` with review-source metadata.

### Add parent-child version comparison endpoint

`GET /api/research/ideas/{idea_id}/version-comparison` will compare a proposal to its parent when one exists. If the proposal has no parent, it returns a current-version summary and `has_parent=false`. The comparison is deterministic and derived from stored proposal fields rather than requiring another model call.

### Board classification uses review package signals

The board will classify proposals with review objections or weak writing readiness into actionable review/revision groups before generic ready-for-writing status. Revised proposals and parent proposals with child versions get explicit signals.

## Risks / Trade-offs

- [Risk] LLM review package is malformed. → Normalize output and provide deterministic fallback from validation, adversarial review, and experiment plan.
- [Risk] Users may confuse validation with review package. → UI labels the package as reviewer-style guidance and keeps validation signals visible.
- [Risk] Board status churn increases. → Keep stable statuses and only add clear blockers/actions.
- [Risk] Version comparison can be noisy. → Use concise field-level comparison rather than full text diff.
