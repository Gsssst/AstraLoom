## Why

Production PDF preview failures can involve several layers: public network reachability, nginx proxying, backend arXiv cache downloads, HTTP range handling, and browser-side pdf.js parsing. A small server-side diagnostic script lets operators capture concrete timing and response-header evidence without changing the running application.

## What Changes

- Add a standard-library Python diagnostic script for PDF proxy URLs.
- Probe DNS/TCP, HEAD, Range GET, normal GET, PDF signature, response headers, first-byte latency, and timeout behavior.
- Print a short interpretation summary for common failure modes.

## Capabilities

### Modified Capabilities
- `deployment-readiness`: Production operators can diagnose PDF proxy behavior with a repo-provided script.

## Impact

- Adds `scripts/diagnose_pdf_proxy.py`.
- No application runtime changes.
