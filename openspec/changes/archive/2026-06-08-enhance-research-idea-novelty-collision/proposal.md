## Why

The current Research Idea Workbench flags novelty using shallow token overlap against the evidence already collected for generation. That is useful as a first pass, but it can miss close prior work that appears in external scholarly search or uses different wording.

This change strengthens proposal quality by adding a visible similar-work collision check before top Ideas are selected.

## What Changes

- Build a similar-work pool for reviewed candidates using the existing local evidence plus external scholarly search when enabled.
- Score candidate collisions with a deterministic combination of lexical overlap, evidence source, recency, and title-level similarity.
- Persist ranked similar-work matches and a collision risk level in each selected Idea's existing review metadata.
- Surface the enriched collision details in the existing validation and Proposal UI signals.
- Keep runs resilient: external search failures SHALL degrade to local evidence without failing Idea generation.

## Capabilities

### New Capabilities

### Modified Capabilities
- `research-idea-generation-v3`: strengthen the novelty check requirement from local token overlap to a multi-source similar-work collision check.
- `research-idea-workbench`: expose enriched similar-work collision details in persisted proposal metadata and workbench UI artifacts.

## Impact

- Backend: `ResearchIdeaWorkbenchService` novelty review and validation helpers.
- Frontend: Research project Proposal detail display for novelty/collision evidence.
- Tests: backend workbench tests and frontend contract tests.
- External services: reuses existing arXiv/Semantic Scholar search services; no new dependency or database migration expected.
