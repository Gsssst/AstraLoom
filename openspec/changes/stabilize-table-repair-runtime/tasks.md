## 1. Parser Runtime Guardrails

- [ ] 1.1 Add table parser failure classification for timeout, OOM/SIGKILL, missing binary, invalid JSON, empty output, and generic non-zero exits.
- [ ] 1.2 Execute external table parser commands in a process group and terminate the group on timeout or cancellation.
- [ ] 1.3 Preserve concise public errors plus longer backend diagnostic excerpts for parser failures.

## 2. Lightweight Repair Fallback

- [ ] 2.1 Implement a lightweight table extraction fallback using existing PDF parsing capabilities where available.
- [ ] 2.2 Merge fallback table blocks with parser metadata and keep quality/repair flags visible.
- [ ] 2.3 Keep Marker high-fidelity repair optional and guarded so local CPU environments can skip it safely.

## 3. Maintenance Job Semantics

- [ ] 3.1 Return a completed-with-failures status when a table repair job processes candidates but repairs none.
- [ ] 3.2 Ensure maintenance progress/result payloads expose actionable parser/runtime failure reasons.

## 4. Verification

- [ ] 4.1 Add backend tests for parser failure classification and subprocess cleanup behavior.
- [ ] 4.2 Add maintenance tests for zero-success table repair job status.
- [ ] 4.3 Run targeted backend tests and record verification results.
