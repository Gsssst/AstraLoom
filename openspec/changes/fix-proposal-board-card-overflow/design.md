## Context

The Proposal progress board renders blocker messages as Ant Design `Tag` elements. Tags default to non-wrapping text, so long Chinese risk messages such as baseline warnings can extend beyond the card and column boundary.

## Goals / Non-Goals

**Goals:**
- Keep board card titles, summaries, signal chips, blocker messages, and actions inside the card.
- Preserve the current board grouping and next-action behavior.
- Avoid broad page redesign.

**Non-Goals:**
- Change board status classification.
- Change backend blocker text.
- Add a new CSS framework or global layout refactor.

## Decisions

- Replace long blocker `Tag` rendering with lightweight inline blocks that allow wrapping and word breaking.
- Add `minWidth: 0`, `maxWidth: 100%`, and `overflowWrap` constraints to card bodies and text areas.
- Keep action buttons wrapping naturally in the card footer.

## Risks / Trade-offs

- Long blockers may make cards taller -> acceptable because vertical growth is preferable to horizontal overflow.
- Inline styles add local specificity -> acceptable for a tightly scoped bugfix in a single page.
