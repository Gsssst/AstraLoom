## Context

The application already has a persistent sidebar, a compact global header, route-level lazy loading, and several workflow-specific search fields. `Ctrl/⌘ + K` currently redirects to the paper library instead of opening a real command surface. External references checked before design:
- GitHub Command Palette exposes a keyboard-opened surface for navigation, search, and commands.
- `cmdk`, `react-cmdk`, and `kbar` style React projects share a pattern of local action registries, keyboard-first selection, grouped results, and optional async search.

The project already uses Ant Design and route prefetch helpers, so the first version can be implemented without adding a new command palette dependency.

## Goals / Non-Goals

**Goals:**
- Provide one global command palette from `Ctrl/⌘ + K` and a visible header button.
- Keep static route/action commands immediately available without waiting for resource search.
- Search lightweight existing resources using current APIs: local papers, research projects, workspaces, and writing projects when available.
- Preserve existing navigation, shortcuts, authentication behavior, and route chunk prefetching.
- Keep the palette usable on narrow screens.

**Non-Goals:**
- Add a backend federated search endpoint.
- Add `cmdk`, `kbar`, or another dependency.
- Implement fuzzy ranking beyond simple local text matching and API-provided result order.
- Replace page-specific detailed search/filter controls.
- Add destructive commands such as delete/archive actions.

## Decisions

- Create a dedicated `GlobalCommandPalette` component mounted inside `BrowserRouter`.
  - Rationale: the component needs `useNavigate` and route context, while still applying globally across public and internal routes.
  - Alternative considered: keep shortcut handling in `App.tsx` and redirect to `/papers`; rejected because it does not solve cross-workflow navigation.

- Use Ant Design `Modal`, `Input`, `List`, `Tag`, and existing icons instead of adding a dependency.
  - Rationale: avoids bundle/dependency growth and matches the current UI system.
  - Alternative considered: adopt `cmdk`; rejected for the first version because AntD can cover the required interaction contract.

- Build commands from a local registry, then append async resource results.
  - Rationale: route/actions are instant and stable, while resource search can be debounced and failure-tolerant.
  - Alternative considered: query the backend for every command; rejected because no unified endpoint exists and it would create unnecessary backend work.

- Reuse existing APIs opportunistically and fail soft.
  - Rationale: command palette search should never block navigation. If resource search fails, static commands remain usable and the palette can show a small unavailable state.
  - APIs: `/papers/search?source=local`, `/research/projects`, `/workspaces`, and writing project listing if an existing endpoint is available.

- Close and navigate on command activation.
  - Rationale: mirrors common command palette behavior and avoids stale overlay state after route transitions.

## Risks / Trade-offs

- [Risk] Multiple resource APIs could make search feel slow.
  -> Mitigation: debounce query, cap result counts, and keep static commands visible immediately.

- [Risk] Resource APIs can return different shapes.
  -> Mitigation: normalize results in the palette component and keep each adapter isolated.

- [Risk] `Ctrl/⌘ + K` may conflict with browser search in some contexts.
  -> Mitigation: only intercept the established app shortcut and keep `/` or browser search untouched.

- [Risk] Public routes may not have authenticated resources.
  -> Mitigation: always show navigation commands and only search resources when authenticated.
