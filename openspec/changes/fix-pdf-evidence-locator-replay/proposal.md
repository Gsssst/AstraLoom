## Why

After clicking a paper-chat evidence marker, the PDF reader can repeatedly scroll back to the localized snippet when the user tries to move to another page. This happens because the same target locator remains in props and can be replayed during later renders.

## What Changes

- Treat each PDF evidence locator request id as one-shot inside the PDF viewer.
- Keep page-only target navigation one-shot as well, so manual scrolling after a jump is not overridden by stale target props.
- Preserve the existing behavior for new evidence clicks: a new request id still jumps to the cited page and attempts snippet localization.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-reader-grounded-interaction`: Evidence localization must not re-run after the user manually scrolls away from a previously localized citation.

## Impact

- Frontend PDF reader locator lifecycle.
- Frontend contract tests for locator replay prevention.
- No backend API or database changes.
