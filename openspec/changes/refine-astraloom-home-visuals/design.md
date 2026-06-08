## Context

The product rename introduced an AstraLoom-specific home page with a star-map/loom visual. After reviewing the rendered page, the user preferred the earlier particle-based home page layout and asked to keep only the name change. The implementation should restore that earlier layout and replace only the old product name with AstraLoom.

## Goals / Non-Goals

**Goals:**

- Restore the earlier home page layout and styling from before the AstraLoom visual redesign.
- Keep `AstraLoom` as the visible product name.
- Keep the existing navigation destinations, copy, and feature scope unchanged.

**Non-Goals:**

- Redesign the home page again.
- Change routing, authentication, backend metadata, or product naming.
- Add new brand assets or external animation libraries.

## Decisions

- Restore from the real git parent of the AstraLoom rename commit.
  This avoids approximating the earlier design and ensures the visual structure matches the previously accepted version.

- Apply only minimal string-level branding updates to the restored home page.
  The user explicitly asked to keep the earlier version and only modify the name, so broader layout or visual changes are out of scope.

## Risks / Trade-offs

- Restoring the earlier page removes the newer star-map AstraLoom-specific composition. Mitigation: the active brand name remains AstraLoom across the restored home page and shared surfaces.
- Tests that asserted the newer visual hooks must be updated. Mitigation: contract tests now check the restored visual hooks and continued AstraLoom naming.
