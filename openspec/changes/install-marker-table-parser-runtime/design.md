## Context

`PDF_TABLE_PARSER_COMMAND` points at `backend/scripts/parse_tables_marker.py`, and that script shells out to `marker_single`. The running backend container has the command configured but does not include the Marker package, so the maintenance action records `marker_single is not installed` for each candidate.

The earlier Marker adapter change intentionally kept Marker optional because it is a heavier parser dependency. This change is the deployment step for environments that want the maintenance button to actually repair low-quality tables.

## Goals / Non-Goals

**Goals:**

- Provide a reproducible dependency declaration for the Marker CLI runtime.
- Preserve the existing parser command and repair API behavior.
- Verify `marker_single` exists in the backend container after installation.

**Non-Goals:**

- Replace Marker with another parser such as MinerU or Docling.
- Change the table quality scoring or merge algorithm.
- Add LLM-assisted Marker correction.

## Decisions

1. Pin the Marker package in an isolated parser environment.
   - Install `marker-pdf` from a dedicated `requirements-marker.txt` into `/opt/marker`.
   - Rationale: `marker-pdf` currently pins OpenAI 1.x while the application `litellm` path requires OpenAI 2.x; isolation keeps the parser runtime from downgrading LLM dependencies.

2. Keep the adapter command unchanged.
   - The existing command remains `python /app/scripts/parse_tables_marker.py --json {pdf_path}`.
   - Rationale: only the runtime executable is missing; the command contract and normalization code are already implemented.

3. Verify through the CLI boundary.
   - Check `/opt/marker/bin/marker_single` in the container and run the adapter help path.
   - Rationale: this validates the exact operational dependency instead of only checking Python package metadata.

## Risks / Trade-offs

- [Risk] Marker increases image build time and size. -> Accept for deployments that enable high-fidelity table repair; keep the parser command configurable.
- [Risk] Marker may need model downloads on first real parse. -> Existing HuggingFace mirror/cache environment remains available to parser subprocesses.
- [Risk] Future Marker releases may change CLI flags. -> Pin the dependency and keep parser verification in the deployment checklist.
- [Risk] The parser virtual environment is missing from `PATH`. -> Set `MARKER_PARSER_BIN` in the image and let the adapter fall back to `/opt/marker/bin/marker_single`.
