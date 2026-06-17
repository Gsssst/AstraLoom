## Context

The PDF reader receives `targetPage` and `targetLocator` props from the paper detail page. React effects run when their dependencies change. The locator effect depends on callbacks that can change identity during parent re-renders, so the same locator object can trigger another scroll even though the user is now manually reading elsewhere.

## Goals / Non-Goals

**Goals:**
- Ensure each target locator request id is consumed at most once.
- Ensure the page-only target jump does not keep forcing the same page after the user scrolls.
- Keep new evidence clicks functional by executing new request ids.

**Non-Goals:**
- Change the locator matching algorithm.
- Add PDF coordinate persistence.
- Change paper-chat reference metadata.

## Decisions

- Track consumed locator request ids in `PDFViewer` refs.
  - Rationale: the PDF viewer owns the actual scroll side effect and can prevent stale replay locally.
  - Alternative considered: clearing parent state after callback. That would still leave timing windows and couples parent state to viewer internals.
- Track the last handled `targetPage` value separately.
  - Rationale: page jumps are also side effects and should execute on a new target value, not on every callback identity change.
  - Alternative considered: removing `targetPage`. It is still useful for page-only navigation when there is no snippet.

## Risks / Trade-offs

- Clicking the same evidence marker twice without changing request id would not re-run.
  - Mitigation: the paper detail page already increments request ids for every click.
- A locator request that starts before pages render may be marked handled.
  - Mitigation: the existing retry loop handles render catch-up for the request before reporting failure.
