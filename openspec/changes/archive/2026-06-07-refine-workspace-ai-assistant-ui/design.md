## Context

The workspace assistant card currently renders quick prompts, message history, visible context references, and the input area in one narrow side column. Long paper titles can overflow the card, and showing every context chip by default consumes too much vertical space before the user starts chatting. The existing app already has a shared `Markdown` component used by the generic chat page.

## Goals / Non-Goals

**Goals:**
- Make the assistant card compact and contained inside the side column.
- Hide context references behind a small expandable control by default.
- Render assistant replies with the shared Markdown component.
- Keep references clickable and scannable when expanded.

**Non-Goals:**
- Change backend assistant context or references.
- Add streaming, new prompts, or new assistant actions.
- Redesign the full workspace detail page.

## Decisions

- Use local component state to toggle context references.
  - Rationale: this is purely visual state and does not need backend persistence.
  - Alternative considered: always show a limited number of references. Rejected because even a few long titles can crowd the card.

- Use existing `Markdown` for assistant messages only.
  - Rationale: assistant answers benefit from lists, headings, and tables; user messages should stay compact plain text.
  - Alternative considered: add another markdown renderer. Rejected because the app already has a shared component.

- Use constrained inline styles for chips rather than adding a new CSS file.
  - Rationale: the assistant card is currently styled inline and the fix is local.
  - Alternative considered: new responsive CSS hooks. Deferred until the assistant layout needs broader responsive reuse.

## Risks / Trade-offs

- [Risk] Markdown tables or code blocks can still be wide.
  -> Mitigation: wrap assistant message content in a container with `maxWidth: 100%` and rely on the shared Markdown table/code overflow handling.

- [Risk] Hidden context could make grounding less visible.
  -> Mitigation: show a compact reference count and make expansion one click.
