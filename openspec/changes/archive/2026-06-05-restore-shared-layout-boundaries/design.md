## Context

The responsive stylesheet defines `.app-layout-main`, `.app-layout-header`, and `.app-layout-content`. Chat intentionally uses `margin: -24px` to fill the padded content area. A visual refresh replaced the application shell markup without retaining those classes, so the negative margin now escapes the content boundary and draws the chat toolbar into the global header.

## Goals / Non-Goals

**Goals:**
- Restore the existing shared shell class contract.
- Keep chat workspace fill behavior inside the intended content region.
- Preserve the visual refresh.

**Non-Goals:**
- Redesign the shell or chat page.
- Change sidebar collapse behavior.
- Refactor unrelated duplicate visual styles.

## Decisions

### Reattach existing shared classes instead of adding page-specific offsets
The responsive stylesheet already defines the intended shell spacing and mobile overrides. Restoring the class names keeps one source of truth and avoids compensating offsets in the chat page.

### Add a static shell contract test
A lightweight source assertion catches future shell rewrites that accidentally remove required classes while leaving dependent page styles in place.

### Let the compact logo occupy the full sidebar width
The collapsed logo click target and its row will span the available sidebar width. The existing flex alignment can then center the icon reliably instead of centering it inside a shrink-to-content wrapper.

### Use one active-session marker
The responsive stylesheet owns the short active-session marker through `::before`. The legacy full-height `border-left` from the home stylesheet will be removed so selected sessions display one visual indicator.

## Risks / Trade-offs

- [Content spacing changes on other pages] → This restores the previously established responsive contract; verify the production build and route shell response.
