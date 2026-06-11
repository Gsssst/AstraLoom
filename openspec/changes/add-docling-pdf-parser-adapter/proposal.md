## Why

The app now has a generic advanced PDF parser interface, but operators still need a concrete adapter before they can use a proven parser without writing their own wrapper command. Docling is a good first adapter because its GitHub/docs expose a Python `DocumentConverter` API and Markdown/structured document exports for PDF parsing.

## What Changes

- Add `docling` as an optional `PDF_STRUCTURED_PARSER_BACKEND` value.
- Use Docling's Python API when installed to convert PDFs and normalize its document output into structured evidence blocks.
- Extract usable text, table, picture/caption, formula, and Markdown evidence from common Docling document shapes.
- Preserve lightweight fallback when Docling is not installed or conversion fails.
- Keep HuggingFace mirror/cache environment configuration active before Docling conversion.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-reader-grounded-interaction`: Advanced paper evidence can be produced by a configured optional Docling parser backend.
- `deployment-readiness`: Deployments can enable Docling parsing without making Docling a required base dependency.

## Impact

- Affects backend structured PDF parsing only.
- Adds tests with fake Docling modules/objects, avoiding a real Docling install in CI.
- No new required dependency, no migration, and no frontend changes.
