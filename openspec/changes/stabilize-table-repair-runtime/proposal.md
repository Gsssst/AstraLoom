## Why

The low-quality table repair action now reaches the Marker runtime, but Marker `TableConverter` is OOM-killed in the local Docker CPU environment even for a single page. Administrators see every candidate fail without actionable diagnostics, and failed parser subprocesses can leave residual processes behind.

GitHub review of adjacent research-assistant projects shows a safer pattern: general research agents such as GPT Researcher use PyMuPDF-style text extraction rather than precise table reconstruction, while paper-focused systems such as PaperQA2 separate lightweight PDF readers from heavier Docling/Nemotron readers. Our maintenance center should follow that layered approach instead of treating a high-memory visual parser as the default batch repair path.

## What Changes

- Add runtime guardrails for table repair so known high-memory parser failures are detected and reported clearly.
- Make table repair cleanup robust when the parser times out or is killed.
- Add a lightweight fallback path for table repair where feasible, using existing PDF text/table extraction capabilities before invoking Marker.
- Preserve Marker as an optional high-fidelity parser, but do not let it silently turn a maintenance run into `success: 0 failed: N` without an explicit resource/compatibility reason.
- Improve job result semantics and diagnostics so maintenance UI can distinguish completed-with-failures from successful repairs.

## Capabilities

### New Capabilities

- `table-repair-runtime-stability`: Runtime stability and diagnostics for low-quality table repair jobs.

### Modified Capabilities

- `paper-library-maintenance-center`: Maintenance center table repair results must expose actionable status when all repair candidates fail.
- `paper-reader-grounded-interaction`: Structured table repair must degrade gracefully when high-fidelity parsers are unavailable or unsafe to run.

## Impact

- Backend table repair command adapter and subprocess management.
- Paper structured parsing and table repair service paths.
- Celery maintenance task progress/result payloads.
- Tests for parser failure classification, fallback behavior, and maintenance result status.
