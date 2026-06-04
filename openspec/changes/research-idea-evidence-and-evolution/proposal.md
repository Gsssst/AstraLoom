## Why

The Research Idea Workbench can now turn local-library evidence into inspectable proposals, but it can still miss recent related work and gives users no disciplined way to narrow, compare, or refine promising directions. The next stage adds optional external scholarly evidence and a lightweight proposal evolution loop so the workbench supports research decisions rather than only generation.

## What Changes

- Add an optional external scholarly-search mode for Idea runs using arXiv and Semantic Scholar adapters.
- Merge external results into the Evidence Map with explicit provenance, stable external identifiers, source URLs, and failure-tolerant fallback to the local paper library.
- Allow users to pin promising proposals, reject weak proposals, and restore a decision without deleting history.
- Add a structured side-by-side comparison view for two to four proposals.
- Allow a pinned or draft proposal to evolve into a new proposal version using its evidence, review uncertainty, experiment plan, and optional user focus.
- Preserve the parent proposal and persist the evolution rationale so proposal history remains inspectable.

## Capabilities

### New Capabilities

- `research-idea-evidence-and-evolution`: Optional external scholarly evidence, proposal decisions, structured comparison, and traceable single-step evolution.

### Modified Capabilities

None.

## Impact

- Extends workbench run configuration and evidence collection with external-search scope and provenance.
- Adds parent-version and evolution metadata fields to persisted research ideas.
- Adds proposal decision, comparison, and evolution API endpoints under the existing authenticated research API.
- Updates the Research Idea Workbench interface with an external-search control, evidence-source labels, selection controls, comparison view, and evolution actions.
- Adds backend regression coverage for external-search degradation, proposal ownership, decision updates, comparison, and evolution persistence.
