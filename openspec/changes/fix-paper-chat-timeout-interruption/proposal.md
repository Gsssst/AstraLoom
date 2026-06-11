## Why

Paper-detail AI Q&A frequently shows "回答生成中断" even when the model is still producing a valid long answer. The root cause is that thinking-enabled paper Q&A currently applies a 30 second timeout to the entire primary stream, so normal long answers are interrupted by our server-side timeout rather than by a real upstream failure.

## What Changes

- Change paper Q&A thinking-stream timeout from an entire-stream hard limit to a first-visible-answer guard.
- Keep the existing recovery path when the primary stream produces reasoning but no visible answer content.
- Continue to mark genuine late upstream failures as interrupted, but stop self-interrupting healthy long answers.
- Add regression coverage for slow thinking-enabled answers that emit content after the first guard window.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-chat-turn-reliability`: Thinking-enabled paper Q&A must not interrupt normal long answers solely because the overall stream exceeds the first-answer timeout.

## Impact

- Affects paper-detail streaming Q&A backend timeout logic and regression tests.
- No API shape change, database migration, or frontend contract change.
