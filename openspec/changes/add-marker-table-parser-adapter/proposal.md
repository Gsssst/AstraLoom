## Why

The high-fidelity table repair pipeline is wired, but it still requires a real parser command. Users should not have to invent a script path; the project should provide a concrete Marker-compatible adapter that can be used directly in `.env`.

## What Changes

- Add a `backend/scripts/parse_tables_marker.py` command that runs Marker table extraction when Marker is installed.
- Normalize Marker JSON/Markdown/HTML output into the table repair command contract: `{"tables":[...]}` with rows/cells/page/caption/confidence.
- Pass `PDF_TABLE_PARSER_*` settings through Docker Compose for backend and worker services.
- Add tests for the adapter's normalization helpers and command contract.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: High-fidelity table repair SHALL have a concrete Marker adapter command available for deployment configuration.

## Impact

- Adds one backend script and tests.
- Docker Compose now forwards `PDF_TABLE_PARSER_COMMAND`, timeout, and max output settings.
- Marker remains optional; if it is not installed, the script exits with an actionable error.
