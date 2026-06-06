## Context

Research Idea Workbench runs already persist `status`, `stage`, `progress`, `message`, `error`, and artifacts, and the stream endpoint forwards stage/artifact/done events to the browser. The current stream lifecycle starts a background task and waits for it in `finally`, so a browser-side abort can still leave the user waiting and does not clearly persist a user-cancelled state.

Similar open research agent projects such as AI-Scientist-style and deep-research-style systems treat proposal generation as a staged long-running pipeline. The useful pattern for this project is to keep the existing staged pipeline, but make the orchestration controllable and recoverable at the UI/API boundary.

## Goals / Non-Goals

**Goals:**
- Let users stop a running candidate Proposal generation from the research project page.
- Persist stopped runs as `cancelled` with a clear message and without a generic failure error.
- Keep failed runs visible with the last stage, reason, and retry action.
- Make completed runs point users toward the generated Top Proposal and next workflow action.
- Preserve the existing stage sequence, artifacts, and idea persistence.

**Non-Goals:**
- Rebuild the Research Idea Workbench generation algorithm.
- Add distributed worker cancellation across multiple server processes.
- Change LLM provider behavior or model routing.
- Introduce a new job queue or database migration.

## Decisions

- Add an authenticated cancel endpoint for project-owned idea runs.
  - Rationale: a browser abort is enough to stop the local fetch, but a durable endpoint lets the UI explicitly mark the latest run as stopped and reload that state later.
  - Alternative considered: rely only on `AbortController`; rejected because persisted state would remain less deterministic.
- Cancel the stream task when the client disconnects or the frontend aborts.
  - Rationale: the stream endpoint owns the in-process task it starts, so it can avoid waiting for the whole generation after the client has gone away.
  - Alternative considered: continue generation in the background; rejected for this interaction because the user is explicitly stopping the run.
- Use `status="cancelled"` instead of overloading `failed`.
  - Rationale: user-initiated cancellation is not a model or pipeline failure and should not show failure styling or retry copy as an error.
  - Alternative considered: store cancellation in `error`; rejected because it confuses telemetry and user-facing recovery.
- Reuse the current frontend SSE parser and add `AbortController` state around it.
  - Rationale: the chat page already uses this pattern and it avoids new dependencies.

## Risks / Trade-offs

- [Risk] Cancellation during an awaited LLM/network call may only take effect after the await yields.
  -> Mitigation: cancel the asyncio task and persist the cancelled state in the endpoint cleanup path.
- [Risk] If the server process restarts during a run, the run may remain `running`.
  -> Mitigation: this change improves interactive cancellation but does not introduce a cross-process watchdog; the persisted latest-run UI still shows the last known stage.
- [Risk] A cancelled task could race with a successful completion.
  -> Mitigation: only mark cancellation for runs whose status is still `running`, and keep completed runs intact.
