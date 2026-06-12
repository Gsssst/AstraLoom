## 1. Evidence Strategy Design

- [x] 1.1 Add explicit paper evidence strategy detection for compact, table, and experiment questions.
- [x] 1.2 Add broad experiment intent terms for Chinese and English experiment/evaluation/result questions.

## 2. Experiment Dossier Retrieval

- [x] 2.1 Build a table catalog from structured table/caption blocks with page, parser, table index, inferred caption, columns, row count, and quality metadata.
- [x] 2.2 Add experiment dossier evidence containing the full table catalog and section-aware experiment text snippets.
- [x] 2.3 Add full table packs for selected experiment-related tables without truncating selected table bodies.
- [x] 2.4 Return distinguishable evidence types and retrieval scope for experiment dossier mode.

## 3. Q&A Context Integration

- [x] 3.1 Use the adaptive strategy budget from current-paper Q&A context construction.
- [x] 3.2 Label `experiment_dossier` and `table_catalog` evidence in prompt context and references.

## 4. Verification

- [x] 4.1 Add regression tests for strategy routing and broad experiment dossier construction.
- [x] 4.2 Add tests that all table catalog entries are present while selected table bodies remain complete.
- [x] 4.3 Run OpenSpec validation, targeted backend tests, and diff checks.
- [x] 4.4 Commit the change.
