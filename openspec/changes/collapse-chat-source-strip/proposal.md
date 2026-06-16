## Why

Chat source strips can become taller than the answer when Research Scout returns ten or more paper candidates. This pushes the useful answer content away and repeats the same problem already fixed for tool traces.

## What Changes

- Collapse chat source/reference strips by default.
- Show a compact one-line summary with source type, count, and the first source label.
- Let users expand the strip to inspect and open every source tag.
- Preserve Research Scout filtering so paper-scout messages still hide generic web references.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `chat-workspace-visual-refinement`: Chat reference/source strips SHALL render as compact collapsed metadata by default and expand only when the user asks to inspect all sources.

## Impact

- Frontend chat message rendering and responsive styles.
- Frontend contract tests.
- No backend, database, or API changes.
