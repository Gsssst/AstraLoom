## Context

The app now lazy-loads route pages, which dramatically reduces the initial application chunk. That split introduces a predictable first-navigation cost: when a user clicks a sidebar item or workflow guide action for a route not loaded yet, the app shows the route fallback while the corresponding chunk downloads.

Reference scan:
- Remix and React Router ecosystems commonly use intent-based prefetching, such as hover/focus prefetch for links.
- Vite dynamic imports can be invoked directly to warm the browser module cache before React renders the lazy component.

## Goals / Non-Goals

**Goals:**
- Centralize route lazy loaders and route chunk prefetch mapping.
- Trigger chunk prefetch from high-intent navigation surfaces: desktop sidebar, mobile drawer menu, homepage quick actions, and workflow guide route actions.
- Deduplicate in-flight/completed prefetches.
- Keep all route paths and lazy route behavior unchanged.

**Non-Goals:**
- Prefetch backend data or call APIs.
- Add a service worker, router plugin, or external prefetch dependency.
- Prefetch every route automatically on page load.
- Change access control; admin-only routes remain visible/prefetched only where the menu already exposes them.

## Decisions

- Create `frontend/src/routes/lazyRoutes.tsx`.
  - Rationale: `App.tsx` and navigation components need a single source of truth for route dynamic imports and prefetch behavior.
  - Alternative considered: duplicate `import('./pages/...')` calls in each component; rejected because route coverage would drift.

- Prefetch on intent events, not on initial load.
  - Rationale: hover/focus/touch start usually indicates likely navigation while avoiding immediate bandwidth cost for all routes.
  - Alternative considered: prefetch all major pages after boot; rejected because users may not visit most modules.

- Deduplicate by normalized route key.
  - Rationale: multiple menu entries and guide steps may point to the same route; repeated dynamic imports should be avoided.
  - Alternative considered: rely on browser/module cache only; rejected because explicit dedupe keeps logic and tests clearer.

## Risks / Trade-offs

- [Risk] Hover prefetch can download chunks the user does not end up opening.
  -> Mitigation: only bind prefetch to deliberate navigation controls, not passive text or every card.
- [Risk] Dynamic routes like `/papers/:paperId` cannot be matched by exact path strings from UI actions.
  -> Mitigation: normalize route prefixes such as `/papers/<id>` to the corresponding registered loader.
- [Risk] Prefetch errors should not break navigation.
  -> Mitigation: swallow prefetch errors and let normal lazy route loading handle failures later.
