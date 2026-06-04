# Change: Workspace resource picker

## Why

The workspace detail page currently asks users to paste resource ids when binding papers, research projects, or writing drafts. This is technically functional but awkward: users have to leave the workspace, find an id, copy it, return, and paste it. A workspace should provide a searchable picker for attachable resources.

## What Changes

- Add a unified workspace resource candidate search endpoint.
- Mark already-linked resources as linked in candidate results.
- Replace the id-only resource binding form with a searchable resource picker.
- Preserve the manual id fallback for edge cases.

## Impact

- Workspace service gains cross-resource search helpers.
- Workspace detail page gains an interactive selection workflow.
- Existing link/unlink APIs remain unchanged.
