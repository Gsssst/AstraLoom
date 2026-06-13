## 1. Pipeline State Normalization

- [x] 1.1 Add a helper to compute active metadata that should be cleared because the artifact is already ready.
- [x] 1.2 Ensure `process_paper` claims queued work before choosing steps and does not let queued metadata suppress missing work.
- [x] 1.3 Ensure reconciliation only skips fresh real `running_steps`, not queued-only metadata.

## 2. Regression Coverage

- [x] 2.1 Add tests for queued-only papers being selected by reconciliation.
- [x] 2.2 Add tests for `process_paper` executing missing queued work.
- [x] 2.3 Add tests for ready artifacts clearing obsolete active metadata.

## 3. Verification and Commit

- [x] 3.1 Run targeted backend tests.
- [x] 3.2 Run strict OpenSpec validation.
- [x] 3.3 Restart backend workers if needed and repair the currently stuck metadata.
- [x] 3.4 Commit the completed fix.
