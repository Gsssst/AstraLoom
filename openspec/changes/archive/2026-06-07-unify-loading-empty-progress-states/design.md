## Context

The primary workflow pages use several state-feedback patterns: `Spin` wrappers, card `loading` props, raw `Empty` states, full-page early returns, and local progress widgets. This makes the app feel inconsistent and can hide the PageShell context during initial loads. Recent error recovery work introduced shared persistent failure feedback; loading, empty, and progress states should receive the same treatment.

GitHub reference scan:
- Ant Design and Ant Design Pro rely on `Skeleton`, `Spin`, `Empty`, `Result`, and `Progress` as the standard primitives for page and data states.
- `react-loading-skeleton` popularizes the useful rule that skeletons should adapt to the real layout instead of creating a separate fake loading screen.
- We will not add a new dependency; the existing Ant Design stack covers the needed states.

## Goals / Non-Goals

**Goals:**
- Add shared state-feedback primitives for PageShell-compatible loading, empty, and progress experiences.
- Keep primary workflow page context visible during initial loading and not-found states.
- Make empty states actionable with a title, description, and optional action.
- Make long-running operations visually distinct from ordinary button loading when progress data or phase text already exists.
- Add contract tests to keep the four primary workflow pages on the shared pattern.

**Non-Goals:**
- Redesign every loading indicator in the app.
- Introduce a new skeleton/loading dependency.
- Change backend task APIs or add new progress endpoints.
- Replace local form validation warnings or small inline loading buttons.
- Build a global task queue or notification system.

## Decisions

- Introduce `WorkflowState` shared components.
  - Rationale: Primary pages need the same language and layout for loading, empty, unavailable, and progress states.
  - Alternative considered: inline `Spin`/`Empty` markup per page; rejected because it continues the current drift.

- Keep PageShell mounted for initial loading and unavailable states.
  - Rationale: Users should retain page identity, navigation context, and next-step framing even while data is loading.
  - Alternative considered: full-page early return; rejected for primary workflows because it feels like a blank transition and hides actions/context.

- Use Ant Design primitives only.
  - Rationale: The app already depends on Ant Design, and its state components cover our needs without bundle or maintenance cost.
  - Alternative considered: `react-loading-skeleton`; rejected because the benefit can be achieved with Ant Design `Skeleton` in this codebase.

- Apply shared components first to high-impact state boundaries.
  - Rationale: Research project initial load/not-found, paper list loading/empty, research direction loading/empty, and writing project empty/progress produce the largest user-facing confusion.
  - Alternative considered: converting every `loading` prop; rejected as too broad for one iteration.

## Risks / Trade-offs

- [Risk] Shared states could become too generic and lose page-specific guidance.
  -> Mitigation: component props require page-specific title/description/action content.
- [Risk] Skeletons that do not match the layout can look like placeholder noise.
  -> Mitigation: provide compact variants and use them only near real list/card surfaces.
- [Risk] Long-running operation progress may still be approximate when backend only exposes phase text.
  -> Mitigation: show known phase/progress when available and avoid inventing fake precision.
