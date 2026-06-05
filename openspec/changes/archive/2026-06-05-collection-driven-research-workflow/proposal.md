# collection-driven-research-workflow

## Why

Paper collections are now available, but they still behave mostly like manual organization. To make them useful for research work, users need to know whether a collection is strong enough for idea exploration, see which collection influenced generated ideas, and place newly discovered external papers directly into the right collection.

## What Changes

- Add collection diagnostics for full-text coverage, embedding coverage, reading progress, and idea-readiness warnings.
- Preserve selected collection metadata when creating a research direction.
- Annotate seed evidence and generated ideas with collection-origin information.
- Allow external search results to be ingested directly into a selected collection.

## Non-Goals

- Automatic collection clustering.
- Shared/team collections.
- Rebuilding the full idea generation algorithm.
- Long-running collection maintenance jobs.

## Reference Patterns

- Zotero-style collections are treated as project context, not only display filters.
- RAG research assistants commonly surface evidence-set health before generation so users understand why outputs may be weak.

## Success Criteria

- A collection can report total papers, full-text coverage, embedding coverage, reading counts, and readiness state.
- The research creation flow can submit selected collection IDs alongside seed papers.
- Idea evidence and persisted idea metadata expose collection names for seed papers.
- Remote search cards can be added directly to a selected collection after ingesting.
