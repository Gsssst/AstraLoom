## Why

Research Idea discussion currently behaves like a shallow chat over a saved title, description, and scores. The workbench already stores evidence, validation, experiment packs, lineage, and evolution data, but those assets are not connected into a coherent AI-assisted idea iteration loop.

## What Changes

- Add an Idea Copilot discussion contract for saved Research Ideas.
- Support explicit Copilot modes: mentor, skeptic, experiment designer, and writer.
- Build Copilot replies from richer context including proposal metadata, evidence, validation summary, execution pack, lineage, evolution metadata, and recent discussion turns.
- Return structured reply metadata: risks, next actions, suggested questions, and an evolution focus.
- Add an endpoint that turns discussion context into a traceable evolved Proposal using the existing evolution mechanism.
- Replace the compact inline discussion area with a cleaner Copilot panel that supports markdown, context chips, quick prompts, mode selection, and discussion-to-evolution actions.

## Capabilities

### New Capabilities
- `research-idea-copilot`: Idea-level AI discussion supports evidence-aware, mode-aware, action-oriented iteration and can convert discussion output into Proposal evolution.

### Modified Capabilities

## Impact

- Affects `backend/app/api/research.py`, `backend/app/services/research_service.py`, `backend/app/services/research_idea_workbench.py`, and Research Project frontend components.
- Adds backend and frontend contract coverage for structured Copilot discussion and discussion-driven evolution.
- No database migration or new external service is required.
- Similar-project research: AI Scientist / AI-Researcher style systems emphasize literature-grounded idea generation, critique, refinement, and ranking; this change applies that pattern to the existing persisted Proposal workflow instead of adding a separate agent system.
