## 1. Marker Adapter

- [x] 1.1 Add `backend/scripts/parse_tables_marker.py` with Marker CLI invocation and output normalization.
- [x] 1.2 Ensure the script emits the high-fidelity table repair JSON contract.
- [x] 1.3 Add clear stderr guidance when Marker is missing or parsing fails.

## 2. Runtime Configuration

- [x] 2.1 Forward `PDF_TABLE_PARSER_COMMAND`, `PDF_TABLE_PARSER_TIMEOUT_SECONDS`, and `PDF_TABLE_PARSER_MAX_OUTPUT_BYTES` in Docker Compose backend service.
- [x] 2.2 Forward the same settings in the Celery worker service.

## 3. Verification

- [x] 3.1 Add tests for Marker adapter output normalization.
- [x] 3.2 Run OpenSpec validation, targeted backend tests, diff checks, and commit.
