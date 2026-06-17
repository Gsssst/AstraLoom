## Why

Paper chat cannot reliably answer questions such as "what is Reference [1]?" because the retrieval planner treats them as ordinary narrow text questions. It often returns body citation contexts like `[11]` instead of the paper's References/Bibliography list.

## What Changes

- Detect reference-list lookup questions in English and Chinese.
- Extract and prioritize the References/Bibliography section from full text or page text.
- When a specific reference number is requested, return the matching bibliography entry and nearby entries as evidence.
- Preserve existing compact retrieval behavior for non-reference questions.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A evidence retrieval must support bibliography/reference-list lookup.

## Impact

- Backend retrieval planner and evidence extraction in `PaperChunkService`.
- Backend tests for paper reader grounded interaction.
- No frontend, database, or API shape changes.
