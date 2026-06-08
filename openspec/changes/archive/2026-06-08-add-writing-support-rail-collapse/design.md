## Context

The current manuscript workbench uses a two-column grid: a 320px support rail and the main editor. This is better than the previous three-column layout, but screenshots show the support rail can still waste width when the user is actively writing.

## Goals / Non-Goals

**Goals:**
- Let users collapse the combined project/evidence support rail.
- Make the editor column use the reclaimed width immediately.
- Keep a visible reopen control when collapsed.
- Avoid adding a layout dependency.

**Non-Goals:**
- Do not make panels draggable/resizable.
- Do not redesign project cards or evidence cards.
- Do not persist the collapsed state across sessions unless existing local state patterns make it trivial.

## Decisions

1. **Use local React state and CSS grid.**
   - Rationale: the workbench already uses a CSS grid and only needs a binary collapsed/expanded state.
   - Alternative: add a resizable panels dependency. That is unnecessary for a simple hide/show interaction.

2. **Keep a narrow collapsed rail instead of removing the column completely.**
   - Rationale: users need an obvious way to bring context back without hunting elsewhere.
   - Implementation note: collapsed rail should be icon/button-first, with short text that does not compete with the editor.

## Risks / Trade-offs

- [Risk] The collapsed rail could still take too much room on small screens.
  -> Mitigation: responsive layout keeps the rail static/single-column under the existing breakpoint.
- [Risk] Hidden evidence/project context may make actions less discoverable.
  -> Mitigation: collapsed state includes a clear restore action and short context summary.
