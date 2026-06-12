## 1. Dependency Wiring

- [x] 1.1 Add the Marker package to an isolated backend parser dependency file with a reproducible version bound.
- [x] 1.2 Confirm Docker backend and worker builds install the isolated parser dependency without changing app LLM dependencies.

## 2. Runtime Verification

- [x] 2.1 Install or rebuild the local backend environment so the configured parser binary points to `marker_single`.
- [x] 2.2 Run targeted parser and maintenance checks for the low-quality table repair path.

## 3. Completion

- [x] 3.1 Record verification results and commit the scoped OpenSpec/dependency changes.

## Verification

- Built and restarted the backend and celery-worker Docker services with the isolated Marker runtime.
- Confirmed backend and worker set `MARKER_PARSER_BIN=/opt/marker/bin/marker_single`.
- Confirmed backend sets `PDF_TABLE_PARSER_COMMAND=python /app/scripts/parse_tables_marker.py --json {pdf_path}`.
- Confirmed `/opt/marker/bin/marker_single --help` and `/app/scripts/parse_tables_marker.py --help` both reach the CLI boundary.
- Confirmed application OpenAI remains on 2.x while the isolated Marker virtualenv carries its own OpenAI 1.x dependency.
- Ran `python -m pytest tests/test_knowledge_base_maintenance.py -q` in the backend container.
