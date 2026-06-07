## Context

The shared `AppLayout` already controls the navigation frame and content area, but pages still implement their own top-level structure. Similar React/Ant Design applications commonly use a page container/header primitive so page content has predictable spacing, title hierarchy, and action placement.

This project does not need a new dependency such as ProComponents for that. A small local `PageShell` component is enough and fits the existing code style.

## Goals / Non-Goals

**Goals:**
- Provide a reusable page shell with title, subtitle, optional icon, actions, and responsive width.
- Keep the shell visually restrained for tool/workbench pages.
- Adopt it in one page to establish the pattern and tests.

**Non-Goals:**
- Redesign every page in this change.
- Change the app sidebar/header layout.
- Replace feature-specific hero sections in chat, research, writing, or paper pages.
- Introduce a third-party layout dependency.

## Decisions

- Add a small component plus CSS rather than inline styles everywhere.
  - Rationale: layout consistency requires stable class hooks and responsive rules.
  - Alternative considered: only add helper constants; rejected because responsive behavior and tests need real class hooks.
- Start with Settings.
  - Rationale: settings is a utility page where a restrained page shell improves consistency without changing the primary research workflows.
  - Alternative considered: update all major pages at once; deferred to avoid a broad visual regression.
- Keep content max width configurable.
  - Rationale: tool pages vary from narrow forms to wide workbenches, so one hard-coded width would be brittle.

## Risks / Trade-offs

- [Risk] Settings page spacing may shift slightly.
  -> Mitigation: keep existing tab/card content intact and only wrap the page.
- [Risk] A generic shell can become too opinionated.
  -> Mitigation: expose only minimal props and class names.
- [Risk] Future pages may adopt inconsistently.
  -> Mitigation: add contract tests that pin the shell hooks and first adoption.
