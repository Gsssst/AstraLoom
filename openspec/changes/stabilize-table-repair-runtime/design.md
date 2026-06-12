## Context

The maintenance center's low-quality table repair path invokes `/app/scripts/parse_tables_marker.py`, which shells out to `marker_single` with `marker.converters.table.TableConverter`. After pre-downloading Marker/Surya models, the parser still fails for every candidate. A manual one-page run exits with code 137 (`Killed`), and process inspection showed Marker consuming most available memory in the Docker CPU environment. The issue is therefore runtime resource pressure, not a missing model download.

Adjacent GitHub projects suggest a layered parser design:

- GPT Researcher exposes a PyMuPDF scraper and does not appear to reconstruct tables as structured cells in its research path. It favors broad text extraction for RAG/reporting.
- PaperQA2 splits PDF ingestion into separate reader packages (`pypdf`, `pymupdf`, `docling`, `nemotron`). Lightweight readers are available independently from heavier document understanding backends.
- Table-specific libraries such as pdfplumber and Camelot use page geometry/text heuristics as a lighter first step; heavier visual/OCR/LLM approaches are optional and environment-sensitive.

Our current implementation put the heaviest visual path directly behind a maintenance button, so batch repair turns into repeated OOM failures.

## Goals / Non-Goals

**Goals:**

- Keep low-quality table repair bounded and diagnosable in local Docker CPU deployments.
- Prevent timed-out or killed parser subprocesses from leaving orphaned `marker_single` processes.
- Add a lightweight repair fallback that can improve table rows without loading Marker.
- Surface completed-with-failures as a distinct maintenance result instead of presenting it as a successful repair.
- Preserve Marker as an optional high-fidelity parser for environments with enough memory/GPU resources.

**Non-Goals:**

- Do not remove Marker support.
- Do not guarantee perfect table reconstruction for complex image-only tables in the lightweight fallback.
- Do not introduce a new large ML dependency in this change.

## Decisions

1. **Use layered table repair.**
   - First run a lightweight parser strategy using existing dependencies (`pdfplumber` when available, with current structured extraction quality gates).
   - Only invoke Marker when the command is configured and runtime guardrails allow it.
   - Rationale: mirrors PaperQA2's reader split and avoids making every local deployment depend on high-memory visual OCR.

2. **Classify parser failures.**
   - Detect timeout, OOM kill (`137`, negative SIGKILL), missing binary, invalid JSON, empty output, and generic non-zero exit.
   - Store concise public messages plus longer diagnostic details in metadata/logs.
   - Rationale: the current 500-1000 character truncation hides the actual failure and makes support impossible.

3. **Kill subprocess groups, not only wrapper processes.**
   - Launch external table parsers in a new process group/session and terminate the group on timeout.
   - Rationale: previous timed-out wrapper processes left `marker_single` children behind.

4. **Make maintenance job status reflect repair outcome.**
   - Keep the Celery task technically successful when it completes its loop, but expose a payload status such as `completed_with_failures` when no candidate repaired successfully.
   - Rationale: Celery success means the task did not crash; the user-facing repair result still needs to show failure.

## Risks / Trade-offs

- [Risk] Lightweight fallback may extract fewer/less accurate cells than Marker. -> Mark repaired blocks with parser metadata and keep quality flags so downstream UI can explain confidence.
- [Risk] Marker may still be desired for high-end environments. -> Keep it configurable and opt-in behind guardrails instead of removing it.
- [Risk] OOM kills can terminate a child before stderr is flushed. -> Classify exit code/signal and show resource-specific remediation guidance.
- [Risk] Process group termination differs by OS. -> Implement Unix path for Docker/Linux and keep a conservative fallback for other platforms.
