## Context

The current chat page already supports session browsing, knowledge-base mode, web search, response depth, exporting, message search, file upload, and prompt shortcuts. The screenshot review showed that these features are visually presented with similar weight, while the destructive clear action is unusually prominent. The page needs visual refinement rather than functional redesign.

## Goals / Non-Goals

**Goals:**
- Establish a calmer hierarchy for the chat title, controls, empty state, sessions, and composer.
- Keep high-frequency actions easy to reach while reducing visual competition.
- Make destructive actions deliberate and confirmed.
- Improve session scanning with compact rows, timestamps, and hover-only deletion.
- Preserve responsive behavior from `responsive-web-experience`.

**Non-Goals:**
- Change chat APIs or persistence.
- Add a new icon library or styling framework.
- Redesign message streaming behavior.
- Refactor unrelated lint issues.

## Decisions

### Use semantic style classes for chat-specific refinements
Add chat-focused classes to the existing responsive stylesheet and keep API logic intact. This keeps the refinement reviewable without starting a broader styling migration.

### Move clear chat into an overflow menu
The toolbar SHALL expose an overflow menu near the title. Clearing the current conversation SHALL remain available but SHALL require confirmation.

### Keep toolbar modes compact and consistent
Knowledge-base mode, web search, response depth, export, and search SHALL appear as a visually related group. Enabled states use a subtle accent rather than competing fills.

### Increase information density in the session sidebar
Use a narrower sidebar, soft active background, a thin active indicator, compact spacing, timestamp text, and hover-only delete affordances.

### Treat the composer as the primary action surface
Prompt shortcuts, upload, input, and send SHALL live inside a rounded composer card with a subtle border and shadow. The empty state SHALL guide the user toward that action surface.

## Risks / Trade-offs

- [Risk] Hover-only delete controls are less discoverable → Keep them visible for the selected session and on mobile.
- [Risk] Overflow menu adds one click for clearing chat → This is intentional because clearing is destructive.
- [Risk] Added CSS specificity can conflict with existing inline styles → Attach explicit classes and only override the necessary visual properties.
