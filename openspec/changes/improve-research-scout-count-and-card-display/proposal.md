## Why

Research Scout currently treats the retrieval depth preset as the requested paper count, so a user asking for 10 or 50 papers can still receive only the standard-depth default. Candidate cards also cap visible cards and allow long venue tags to overflow, making the result feel incomplete and visually broken.

## What Changes

- Parse explicit requested paper counts from the user prompt and distinguish them from internal candidate-pool size.
- Expand Research Scout query planning for video grounding and similar paper-discovery prompts with broader scholarly synonyms.
- Oversample arXiv-first and fallback scholarly providers so the ranked set can satisfy larger requested counts within a bounded maximum.
- Return retrieval metadata that explains requested count, final count, pool size, and whether the request was capped.
- Show all returned Research Scout candidates in the chat UI with a compact expand/collapse control instead of hard-capping cards at six.
- Prevent long venue/provenance/constraint tags from overflowing candidate cards.

## Capabilities

### New Capabilities

- `chat-research-scout-mode`: Research Scout count handling, query planning diagnostics, and bounded candidate recommendations.

### Modified Capabilities

- `paper-discovery-search-and-ingest`: Scholarly discovery SHALL separate final result count from internal candidate pool size and broaden query expansion for topic aliases.
- `chat-workspace-visual-refinement`: Research Scout candidate cards SHALL display bounded long metadata labels and expose returned candidates without a fixed six-card limit.

## Impact

- Backend chat Research Scout intent parsing, query planning, retrieval, metadata, and tests.
- Frontend Research Scout card rendering, CSS, and contract tests.
- No database schema or external dependency changes.
