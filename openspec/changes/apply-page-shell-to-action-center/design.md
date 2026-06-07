## Context

Action Center groups suggested next actions from paper, research, writing, and workspace workflows. It is a dashboard-like utility page and fits the same shared shell pattern as Settings and Workspaces. Its API calls currently use generic error extraction, which loses retryability and recovery guidance available in `getApiErrorDetails`.

## Goals / Non-Goals

**Goals:**
- Adopt `PageShell` without changing grouped action rendering.
- Keep existing summary metrics visible near the top.
- Persist load/action failure details with message, recovery, category, retryability, and optional HTTP status.

**Non-Goals:**
- Change backend workflow action schema.
- Redesign action cards or grouping behavior.
- Add automatic retries or background refresh.

## Decisions

- Render summary statistics as compact cards below the shell header.
  - Rationale: metrics remain visible but no longer require a custom hero.
  - Alternative considered: put metrics in shell actions; rejected because shell actions should stay command-oriented.
- Store one failure detail state for Action Center.
  - Rationale: load and execution failures share the same UI pattern and only one durable recovery alert is needed at a time.
  - Alternative considered: per-action errors; deferred because current actions execute one at a time.

## Risks / Trade-offs

- [Risk] Removing the gradient hero reduces visual emphasis.
  -> Mitigation: keep summary metric cards and a clear shell title/icon.
- [Risk] A single failure state can be overwritten by a later action.
  -> Mitigation: this matches the current single `lastActionResult` behavior and avoids clutter.
