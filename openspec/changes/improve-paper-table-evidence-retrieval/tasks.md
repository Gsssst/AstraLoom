## 1. Parser Quality

- [x] 1.1 Add structured PDF table quality metadata derived from persisted table blocks.
- [x] 1.2 Improve parser status responses and maintenance visibility to show table quality warnings.
- [x] 1.3 Prefer configured advanced parser output for table blocks when available while keeping lightweight fallback.

## 2. Table Evidence Retrieval

- [x] 2.1 Detect table-like paper questions using benchmark/metric/reward/table/result triggers.
- [x] 2.2 Add a dedicated structured table/caption evidence lane and merge it with section/document evidence.
- [x] 2.3 Ensure final evidence references preserve source type, parser source, score, snippet, metadata, and PDF page.

## 3. Verification

- [x] 3.1 Add tests for table quality metadata on low-fidelity and high-fidelity extracted tables.
- [x] 3.2 Add tests for OMTG-style table questions where section-first retrieval must still include table evidence.
- [x] 3.3 Run OpenSpec validation and targeted backend tests.
- [x] 3.4 Commit the change.
