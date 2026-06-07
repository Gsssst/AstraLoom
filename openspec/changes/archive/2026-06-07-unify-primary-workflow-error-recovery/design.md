## Context

The shared `getApiErrorDetails` helper already normalizes backend envelopes, validation errors, timeouts, network failures, and status codes. Several utility pages render those details in persistent Alerts, but primary pages still mostly call `message.error`, which disappears quickly and hides recovery details.

## Goals / Non-Goals

**Goals:**
- Provide one reusable error Alert component for structured API failures.
- Add page-level persistent error state to the four primary workflow pages.
- Convert important API catch paths to `getApiErrorDetails`.
- Keep transient success/info/warning toasts for successful actions and user input validation.
- Preserve all current workflows and API calls.

**Non-Goals:**
- Replace every non-API validation toast.
- Change backend error response formats.
- Add retry buttons for every operation.
- Redesign page layouts beyond inserting a dismissible error Alert.

## Decisions

- Introduce `ApiErrorAlert` instead of repeating Alert markup in each page.
  - Rationale: Action Center, digest, admin, and workspace detail already duplicate the same pattern; a component reduces drift for new primary pages.
  - Alternative considered: inline alerts per page; rejected because this change touches four large pages.
- Use one latest-error state per page.
  - Rationale: users generally need the latest failed operation and recovery guidance; multiple stacked failures would add noise on dense workbench pages.
  - Alternative considered: per-section errors; rejected for this iteration because it would require wider layout changes.
- Keep `message.warning(detail.message)` alongside persistent Alerts for failed API actions.
  - Rationale: the toast gives immediate feedback near the moment of action, while the Alert remains available for recovery details.
- Do not convert intentional input warnings.
  - Rationale: messages like “请填写项目主题” are local validation prompts, not API failures.

## Risks / Trade-offs

- [Risk] A page-level Alert may appear far from the failed control on long pages.
  -> Mitigation: place it near the PageShell body top, where it is consistent and persistent.
- [Risk] Converting many catches could accidentally change loading cleanup.
  -> Mitigation: keep try/finally structure intact and only change error handling statements.
- [Risk] Large pages may still have a few inline API catches after this change.
  -> Mitigation: cover the high-value paths now and add tests that enforce the shared error component and details helper are present.
