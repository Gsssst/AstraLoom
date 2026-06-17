## Why

Paper-chat evidence links currently navigate only to the cited PDF page. Users still need to manually search within that page, which breaks the evidence-inspection loop when the cited page is dense or the answer references a short passage.

## What Changes

- Add a lightweight frontend evidence locator that searches the rendered PDF text layer for the cited snippet after page navigation.
- Scroll the matched text span into view and apply a temporary highlight so users can see the exact passage when available.
- Preserve current page-only navigation as the fallback when the snippet is unavailable, the PDF is in native fallback mode, or the text layer cannot match the snippet.

## Capabilities

### New Capabilities

### Modified Capabilities

- `paper-reader-grounded-interaction`: Paper-chat evidence links should attempt page-internal snippet localization after navigating to the cited page.

## Impact

- Frontend PDF reader and paper detail chat evidence navigation.
- Frontend contract tests for evidence-to-PDF-page localization.
- No backend API, database, or PDF parser changes.
