## 1. Parser Configuration And Normalization

- [x] 1.1 Add `PDF_TABLE_PARSER_COMMAND` and bounded parser output settings to configuration and parser health.
- [x] 1.2 Implement a high-fidelity table parser command runner that reuses HuggingFace mirror/cache subprocess environment.
- [x] 1.3 Normalize common table parser JSON shapes into `StructuredPdfBlock` table blocks with cell metadata.
- [x] 1.4 Parse HTML table output into rows/cells when returned by Marker/MinerU-style parsers.

## 2. Table Quality And Repair

- [x] 2.1 Extend table quality diagnostics for merged numeric cells, inconsistent row widths, malformed Markdown, empty cells, and generic headers.
- [x] 2.2 Add a function that repairs low-quality structured table blocks using high-fidelity parser output while preserving original metadata.
- [x] 2.3 Automatically attempt repair after normal structured parsing when table quality is low and a repair parser is configured.
- [x] 2.4 Persist repair success/failure metadata in `Paper.metadata_json`.

## 3. Maintenance Center Integration

- [x] 3.1 Add backend recommendation logic for low-quality table repair candidates.
- [x] 3.2 Add a bounded admin maintenance endpoint to repair low-quality table parses.
- [x] 3.3 Add frontend maintenance action and status details for table repair candidates.

## 4. Paper Q&A Integration

- [x] 4.1 Prefer repaired table cell metadata when building table evidence blocks.
- [x] 4.2 Include repair source and quality flags in table evidence references.

## 5. Verification

- [x] 5.1 Add tests for parser command normalization, including rows/cells and HTML table output.
- [x] 5.2 Add tests for low-quality detection and repair metadata persistence.
- [x] 5.3 Add tests for maintenance recommendations/actions.
- [x] 5.4 Add tests for Q&A evidence using repaired table blocks.
- [x] 5.5 Run OpenSpec validation, targeted backend tests, frontend build if touched, diff checks, and commit.
