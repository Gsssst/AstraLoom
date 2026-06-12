## Context

The previous change added the command boundary:

```env
PDF_TABLE_PARSER_COMMAND="... {pdf_path}"
```

but no project-owned command existed yet. Marker is a practical first adapter because its documented CLI supports table conversion and JSON output through `marker.converters.table.TableConverter`.

## Goals / Non-Goals

**Goals:**

- Provide a real script path that `.env` can use.
- Keep Marker optional and fail clearly if unavailable.
- Normalize several plausible Marker outputs into the existing table repair JSON contract.
- Ensure Docker services receive the new configuration.

**Non-Goals:**

- Vendor Marker into the repository.
- Force-install large model dependencies in `requirements.txt`.
- Add a MinerU adapter in this change.

## Decisions

1. Use a subprocess CLI fallback first.
   - The script invokes `marker_single` with `TableConverter` and JSON output.
   - Rationale: Marker APIs may shift, while the CLI is the documented operational surface.

2. Keep the adapter output minimal.
   - Output shape: `{"tables":[{"page":..., "caption":..., "rows":[...], "cells":[...]}]}`.
   - Rationale: the backend repair pipeline already normalizes this shape.

3. Keep parser installation separate.
   - Rationale: Marker may download models and has heavy optional dependencies; deployments should opt in.

## Risks / Trade-offs

- [Risk] Marker CLI output format changes. -> Normalize `tables`, `blocks`, `children`, markdown, HTML, and text fallbacks.
- [Risk] Marker is not installed. -> Exit non-zero with a clear install/configuration message.
- [Risk] Docker service misses env vars. -> Forward `PDF_TABLE_PARSER_*` in both backend and celery worker.
