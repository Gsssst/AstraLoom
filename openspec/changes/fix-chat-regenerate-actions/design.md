## Context

The chat page currently implements regeneration menu items by calling `setInput('...')` followed by `setTimeout(() => handleSend(), 100)`. This relies on state timing and can race with input updates, especially under rendering load.

## Goals / Non-Goals

**Goals:**
- Make regeneration actions send deterministic prompt text.
- Keep the existing stream send path and UI behavior.
- Avoid duplicating the send implementation.

**Non-Goals:**
- Implement true model-side regeneration from prior assistant message ids.
- Change conversation history trimming or message persistence.
- Redesign action menus.

## Decisions

- Add an optional `overrideContent` argument to `handleSend`.
  - Rationale: this reuses the existing send path while making programmatic sends deterministic.

- Clear the input only when sending the visible input value.
  - Rationale: a programmatic regeneration prompt should not depend on or unexpectedly erase unrelated draft text unless the action intentionally sets it.

- Remove timeout-based sends from regeneration menu items.
  - Rationale: explicit arguments make the order of operations clear.

## Risks / Trade-offs

- Regeneration actions still append a new user prompt instead of replacing the prior assistant message -> mitigation: this change fixes reliability only and preserves existing product behavior.
