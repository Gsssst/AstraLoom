## Context

The frontend already uses a shared Axios instance in `frontend/src/services/api.ts`, but most pages parse failures locally. Many handlers show generic messages, duplicate parsing logic, or swallow failures entirely. The backend may return either FastAPI validation details, plain `detail` strings, or the app's structured `error.message` envelope, so page code needs a consistent way to turn these shapes into useful Chinese feedback.

This change follows the pattern used by Ant Design Pro-style request handling: centralize error interpretation, keep page-level business context close to the user action, and avoid hiding recoverable failures.

## Goals / Non-Goals

**Goals:**
- Provide one shared frontend helper for extracting user-facing error messages from API failures.
- Give high-frequency workflows clear failure messages for auth, permission, timeout, network, validation, and backend-detail errors.
- Preserve existing behavior and API contracts while improving feedback quality.
- Keep streaming chat error display compatible with existing SSE error events.

**Non-Goals:**
- Redesign every page's loading or empty state in one pass.
- Change backend error schemas.
- Add new toast, telemetry, or error-boundary dependencies.
- Replace all inline `catch` blocks across the repository.

## Decisions

- Add a small frontend utility near the API service layer.
  - Rationale: error parsing depends on Axios/backend response shapes and should not be duplicated in each page.
  - Alternative considered: only enhance the Axios response interceptor. Rejected because many user actions need contextual prefixes like "删除失败" or "检索失败"; a helper lets pages keep that context.

- Parse known backend shapes in priority order.
  - Rationale: the app currently emits `error.message`, `detail` strings, FastAPI validation arrays, and occasionally plain strings. A deterministic order prevents noisy object dumps.
  - Expected order: app envelope message, `detail` string, validation detail summary, plain response string, network/timeout fallback, generic fallback.

- Update only high-traffic pages in the MVP.
  - Rationale: chat, paper library, research directions, and settings account for most user-triggered failures. Broader replacement can follow after the pattern is proven.

- Keep errors concise and actionable.
  - Rationale: the UI should explain what happened and what the user can try, not expose stack traces or raw JSON.

## Risks / Trade-offs

- [Risk] A generic parser may hide useful debugging detail from developers. → Mitigation: preserve original errors in console only where useful and keep backend responses unchanged for network inspection.
- [Risk] Some pages still have older generic messages after the MVP. → Mitigation: scope tasks to critical workflows and leave follow-up replacement as a separate iteration.
- [Risk] Overly long validation summaries can clutter toasts. → Mitigation: summarize validation detail to the first relevant message.
