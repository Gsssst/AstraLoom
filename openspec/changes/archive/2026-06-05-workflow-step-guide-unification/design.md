## Context

The paper library, research direction, writing workbench, action center, and project spaces now contain many useful capabilities, but the frontend still relies on users knowing where to go next. Existing pages use different visual patterns for next actions, so the workflow feels fragmented even when the underlying modules are connected.

## Goals / Non-Goals

**Goals:**
- Introduce a reusable guide component for contextual next-step actions.
- Make paper library, research direction, and writing workbench pages speak the same workflow language.
- Support both route navigation and local page actions without adding new APIs.
- Keep the guide compact so it helps orientation without becoming another dashboard.

**Non-Goals:**
- Rebuild the full workspace dashboard.
- Change backend workflow recommendation APIs.
- Replace existing module-specific controls or writing workbench recommendations.
- Add personalized ranking of next actions in this iteration.

## Decisions

- Use a frontend-only shared component.
  - Rationale: this iteration is about cross-page UI consistency, and the pages already know their local actions.
  - Alternative considered: create a backend workflow recommendation endpoint for every page. That would be more powerful, but it is too heavy for this P8 slice and duplicates the existing action center.
- Keep steps declarative with `title`, `description`, `status`, `actionLabel`, `path`, and optional `onClick`.
  - Rationale: page integrations stay small, and future modules can reuse the component without importing page-specific logic.
  - Alternative considered: hard-code the steps in the component. That would make the first version faster but would not scale across modules.
- Place the guide directly below each hero section.
  - Rationale: it gives orientation before the user drops into detailed tools.
  - Alternative considered: put it in a floating sidebar. That risks layout conflicts with the current responsive app shell.

## Risks / Trade-offs

- [Risk] The guide becomes repetitive if every page shows too many actions. → Mitigation: limit each page to three concise actions.
- [Risk] Local actions can drift from actual page state. → Mitigation: keep labels generic and back them with contract tests that verify the guide remains wired into the pages.
- [Risk] More UI could crowd small screens. → Mitigation: use responsive grid cards that stack vertically on narrow layouts.
