## Context

The frontend uses Ant Design components with many page-local inline styles. Desktop layouts are generally functional, but shared navigation and high-density workspaces rely on fixed widths and horizontal composition. A responsive layer must preserve desktop behavior while making narrow screens usable without introducing a new styling framework.

## Goals / Non-Goals

**Goals:**
- Provide a mobile navigation drawer while preserving the desktop sider.
- Use shared CSS classes for responsive spacing and reflow rules.
- Replace squeezed split panes on paper detail pages with explicit mobile panel switching.
- Keep paper search, authentication, and chat controls usable at phone widths.
- Preserve current routes, API contracts, and desktop workflows.

**Non-Goals:**
- Redesign the visual identity or theme system.
- Add backend APIs.
- Fully redesign every secondary page in one pass.
- Replace Ant Design or migrate all inline styles to CSS.

## Decisions

### Use Ant Design breakpoints at component boundaries
Use `Grid.useBreakpoint()` where rendering behavior changes, such as desktop sider versus mobile drawer and paper detail split view versus mobile panel switching. CSS media queries handle spacing, wrapping, and width adjustments.

This keeps structural decisions explicit while avoiding JavaScript for simple presentation changes.

### Keep desktop composition stable
Desktop users retain the expanding sider, split paper reader, and inline chat sessions list. Mobile users receive purpose-built alternatives only below the medium breakpoint.

This lowers regression risk and allows incremental improvements.

### Add one shared responsive stylesheet
Add a frontend stylesheet for layout classes used across the touched pages. Continue using local inline styles for component-specific visuals.

This is smaller and easier to review than introducing a CSS module migration or a new utility framework.

### Use panel switching for mobile paper reading
On mobile, paper metadata, PDF, and AI Q&A SHALL occupy the full available width one at a time. The toolbar exposes explicit panel buttons.

A stacked PDF and Q&A experience would make each workspace too short to use comfortably.

### Use an overlay drawer for mobile chat sessions
On mobile, the conversation list SHALL not permanently consume horizontal width. It opens as a drawer from the chat toolbar and closes after a session is selected.

## Risks / Trade-offs

- [Risk] Responsive CSS overrides can diverge from inline styles → Use targeted classes and limit `!important` to fixed-width overrides that cannot otherwise be changed at a breakpoint.
- [Risk] Mobile panel switching can hide useful context → Keep switching controls visible in the paper detail toolbar.
- [Risk] Chat toolbar still contains many actions → Allow wrapping and hide only non-essential search input on very narrow screens.
- [Risk] Automated browser inspection is currently blocked by the local browser policy → Verify compilation and static responsive rules, then retain a manual visual pass as residual validation.
