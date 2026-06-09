## Context

The backend PDF proxy can return a valid `application/pdf` body, but the production reader can still fail inside pdf.js. The current viewer passes a relative URL string directly to `Document` and relies on pdf.js' generic fallback error UI, which makes production debugging difficult.

## Goals / Non-Goals

**Goals:**
- Keep PDF loading compatible with same-origin Nginx deployments.
- Provide a stable file input for `react-pdf`.
- Show a concise frontend error message instead of only pdf.js' generic text.

**Non-Goals:**
- Replacing react-pdf/pdf.js.
- Changing backend PDF download or arXiv cache logic.
- Adding authenticated PDF endpoints.

## Decisions

- Resolve relative PDF URLs against `window.location.origin` before passing them to `Document`.
- Pass `file={{ url: resolvedUrl }}` so pdf.js receives an explicit URL descriptor.
- Track `onLoadError` and render an Ant Design alert with the failed URL and error message.

## Risks / Trade-offs

- The frontend cannot prove whether the response body is a PDF without fetching it twice -> rely on pdf.js error and backend curl diagnostics.
- If the worker asset itself is blocked, the error may still come from pdf.js -> exposing the message gives operators a faster clue.
