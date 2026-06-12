## Context

The current parser stack supports:

- `docling` when installed.
- `command` for a generic external parser.
- `pdfplumber` lightweight fallback.

This is useful for broad structure, but exact table-value questions fail when the table block is already corrupted. The system currently stores table text mostly as Markdown; if numeric cells are merged or headers are generic, downstream retrieval can only quote bad evidence.

External project patterns:

- Marker exposes table-specific conversion and optional LLM correction, with JSON outputs and cell-level information.
- MinerU exposes structured Markdown/JSON/HTML and is designed for complex PDFs, including table/formula/OCR cases.
- Docling supports advanced PDF layout, reading order, table structure, and lossless JSON-style export.
- RAGFlow treats document parsing quality, chunk visibility, and references as operational surfaces, not hidden implementation details.

## Goals / Non-Goals

**Goals:**

- Add a table-specialized repair path for low-quality table blocks.
- Persist cell-level table structure in metadata without requiring a schema migration.
- Let administrators see and repair low-quality table parses from the maintenance center.
- Prefer repaired table evidence during paper Q&A.
- Keep all HuggingFace-dependent subprocesses on the configured mirror environment.

**Non-Goals:**

- Bundle or install Marker/MinerU/Docling dependencies automatically in this change.
- Guarantee perfect recovery for every visually complex PDF.
- Build manual table editing UI in this iteration.
- Perform pixel-level figure understanding beyond what external table parsers return.

## Decisions

1. Add a dedicated high-fidelity table parser command.
   - Setting: `PDF_TABLE_PARSER_COMMAND`.
   - Contract: command receives `{pdf_path}` and returns JSON with tables/cells/headers/caption/page/confidence.
   - Rationale: Marker, MinerU, and local scripts have different Python APIs and dependency footprints; a JSON command boundary keeps the app stable.

2. Normalize high-fidelity parser output into existing structured blocks.
   - Table blocks keep Markdown text for current retrieval compatibility.
   - Metadata stores `cells`, `headers`, `row_count`, `column_count`, `caption`, `confidence`, `quality_flags`, `repair_source`, and optionally `bbox`.
   - Rationale: retrieval can use clean Markdown now, while future UI can render/edit cell structures.

3. Run repair selectively.
   - Normal parsing still runs first.
   - If table quality is low, or a table-value Q&A hits low-quality evidence, the repair path can be invoked.
   - Rationale: high-fidelity parsing is slower and sometimes needs heavier dependencies, so it should be targeted.

4. Improve quality scoring.
   - Add merged numeric-cell detection, inconsistent row width, missing headers, generic headers, and malformed Markdown signals.
   - Rationale: "low quality" must catch cases like RULER table 3 where values are visibly present but not cell-reliable.

5. Expose repair through maintenance APIs.
   - Existing `/maintenance/backfill-structured-pdf` remains.
   - Add a table repair recommendation/action that targets papers with ready structured parse but poor table quality.
   - Rationale: administrators need a queue specifically for bad tables, not only missing parses.

## Risks / Trade-offs

- [Risk] External table parser is not configured. -> Report parser health and keep the normal structured parse result, with actionable maintenance guidance.
- [Risk] Parser output formats differ. -> Normalize common shapes: `tables`, `blocks`, `pages`, `cells`, `rows`, `html`, and `markdown`.
- [Risk] High-fidelity repair may still fail. -> Persist visible failure metadata and keep original blocks available.
- [Risk] Prompt size can grow. -> Store full cell structures in metadata but keep Q&A evidence bounded by strategy-specific retrieval budgets.
