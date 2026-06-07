## Context

The research project page already exposes Proposal lineage, validation, execution pack, experiments, and Copilot discussion. These views are useful but fragmented. The backend has enough persisted data to derive a timeline without adding storage: `created_at`, `parent_idea_id`, `evolution_json`, `discussion_log`, `review_json`, `experiment_plan`, validation output, execution pack output, and project experiments.

## Goals / Non-Goals

**Goals:**
- Provide one read-only timeline endpoint for an accessible Proposal.
- Include bounded, human-readable events for creation, evolution, Copilot discussion, validation, execution readiness, linked experiments, and child versions.
- Add a focused frontend timeline drawer with event categories and actionable summaries.
- Reuse existing validation, execution pack, lineage, and experiment services.

**Non-Goals:**
- Add editable notes or manual timeline events.
- Add a new normalized event table.
- Replace existing validation, execution pack, Copilot, or lineage views.
- Trigger model calls while building the timeline.

## Decisions

- **Derive events on demand.** Timeline data should be assembled from existing persisted records so no migration is needed and historical data becomes visible immediately.
- **Use stable event types.** The API returns `type`, `title`, `summary`, `timestamp`, `severity`, `tags`, and `details` so the frontend can render consistently while still allowing richer payloads.
- **Bound noisy discussion logs.** Copilot discussion entries should be collapsed into assistant milestones with mode, risks, next actions, suggested questions, and evolution focus instead of displaying every raw token-sized message.
- **Reuse project experiment lookup.** Experiment events should use `ExperimentService.get_experiments(project_id)` and filter by `idea_id`, matching the execution pack behavior.

## Risks / Trade-offs

- Derived timestamps are imperfect for JSON-only discussion entries -> use idea `created_at` as fallback and keep ordering stable.
- Timeline payload can become large for long discussions -> bound discussion milestones to recent/high-value assistant entries.
- Timeline may duplicate information shown elsewhere -> keep it summary-oriented and link users back to detailed actions.
