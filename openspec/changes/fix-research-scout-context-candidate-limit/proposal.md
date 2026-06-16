## Why

Research Scout can retrieve and rank more than eight papers, but the final answer context still truncates candidate metadata to the first eight papers. This makes the model repeatedly say only eight candidates are available even when the user requested ten or more and the backend has more ranked candidates.

## What Changes

- Replace the fixed eight-paper final answer context cap with a bounded dynamic context limit derived from the requested final result count and actual candidate count.
- Include explicit context-count diagnostics so the final model knows how many candidates were retrieved, how many are included in the prompt, and whether the result set is genuinely underfilled.
- Add a regression test proving a ten-paper Research Scout request exposes ten candidates to the final answer context.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `chat-retrieval-mode-coordination`: Research Scout final answer context SHALL expose enough candidate metadata to satisfy the requested count when candidates are available, instead of hard-capping final-answer evidence at eight.

## Impact

- Backend Research Scout answer context formatting and prompt diagnostics.
- Focused backend regression tests.
- No database schema, external API, or frontend contract changes.
