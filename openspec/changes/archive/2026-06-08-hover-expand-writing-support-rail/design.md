## Context

The writing manuscript workbench already has a compact project/evidence support rail and a full-width editor area. The current behavior requires clicking the fold/unfold control, so users who want maximum writing width must manually collapse it and manually expand it again.

The main app layout already uses a hover-expand sidebar pattern on desktop. The writing support rail should follow the same interaction model while preserving touch accessibility.

## Goals / Non-Goals

**Goals:**
- Default the support rail to a compact icon-only state on desktop.
- Expand the rail while the mouse is over the rail, and collapse it when the mouse leaves.
- Keep the existing project list and evidence cards available without changing backend data loading.
- Keep a click affordance so mobile/touch users can still expand the rail.

**Non-Goals:**
- Rebuild the writing project panel.
- Add persistent user preferences for rail width.
- Change evidence card data or writing project APIs.

## Decisions

- Reuse the existing `supportRailCollapsed` state and collapsed rail components instead of introducing a new sidebar component.
- Add hover handlers to both collapsed and expanded support rail wrappers so the transition is reversible without requiring a click.
- Preserve the explicit fold/unfold buttons as accessibility/touch affordances even though hover becomes the primary desktop behavior.
- Keep responsive CSS overriding the layout to one column below the existing breakpoint.

## Risks / Trade-offs

- Hover does not exist on touch devices -> keep explicit expand/collapse controls.
- Fast pointer movement could briefly resize the editor -> retain the current 64px/320px grid widths and transition only the existing grid state.
- Users may want a pinned expanded rail later -> defer persistent pinning until there is a clear need.
