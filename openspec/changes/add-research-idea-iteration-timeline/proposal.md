## Why

Idea Copilot can now turn discussions into Proposal evolution, but users still need to inspect multiple places to understand how a Proposal changed: discussion log, validation, execution pack, experiment feedback, and lineage are separate views. A unified iteration timeline will make idea maturation auditable and easier to continue.

## What Changes

- Add a Proposal iteration timeline API that summarizes creation, parent evolution, Copilot discussion milestones, validation state, execution readiness, linked experiments, and child versions.
- Add a focused frontend timeline view opened from Proposal cards and the Copilot panel.
- Surface concise event details, next actions, risks, and version relationships without requiring users to manually inspect each underlying panel.
- Keep the timeline read-only and derived from existing records.

## Capabilities

### New Capabilities
- `research-idea-iteration-timeline`: Saved Proposals expose a unified, read-only timeline of discussion, validation, experiment, and evolution events.

### Modified Capabilities

## Impact

- Affects `backend/app/api/research.py`, `backend/app/services/research_service.py`, `frontend/src/pages/ResearchProjectPage.tsx`, and focused tests.
- No database migration or new dependency is required.
- Similar-project research: AI Scientist / AI-Researcher style systems preserve idea review and refinement history, while research-agent tracing projects emphasize interaction/event traces; this change applies that pattern to the persisted Proposal lifecycle already present in this project.
