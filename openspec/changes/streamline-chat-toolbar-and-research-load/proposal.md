## Why

The chat toolbar currently places model metadata, capability badges, retrieval mode controls, export, and search in one crowded row. The research project detail page also waits for secondary recommendation data before leaving the full-page loading state, so opening a direction can feel slow even when the core project data is available.

## What Changes

- Simplify the chat toolbar by keeping primary controls visible and moving detailed status/secondary actions into compact menus.
- Preserve existing chat capabilities: model visibility, knowledge-base toggle, web toggle, search depth, export, conversation search, and clear confirmation.
- Load research project core data independently from secondary related-paper recommendations.
- Show related-paper loading in its own panel without blocking the whole research workbench.

## Capabilities

### New Capabilities

### Modified Capabilities
- `chat-workspace-visual-refinement`: Chat toolbar controls must remain compact and scannable across common desktop widths.
- `research-idea-workbench`: Research project pages must render core workbench content without waiting for slow secondary recommendation data.

## Impact

- Frontend chat toolbar layout and responsive CSS.
- Frontend research project page data loading sequence.
- Frontend contract tests for toolbar and workbench loading behavior.
