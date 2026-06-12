## Why

Paper Q&A still misses evidence when the user asks broad experimental questions such as "analyze the whole experiment", "compare all results", or "use all tables". The current table path improves local table lookup, but it still treats broad experiment analysis as a small top-k retrieval problem.

Related GitHub projects point to a better pattern: RAGFlow uses multiple recall paths and traceable references, Docling/MinerU/Marker preserve structured document/table units, and LlamaIndex's recursive table retrieval routes table hits into table-specific query context instead of flattening everything into anonymous chunks.

## What Changes

- Add question-type routing for current-paper Q&A: compact factual, local table, broad experiment/evaluation, and section-focused retrieval.
- Add an experiment evidence dossier for broad experiment/evaluation questions.
- Include a table catalog for all available tables in broad experiment mode, with page, parser source, table index, inferred caption, columns, row count, and quality flags.
- Include complete bodies for the selected experiment-related table packs; selected table bodies must not be character-truncated.
- Add several experiment/evaluation/results text snippets and limited conclusion/limitation snippets to support narrative analysis around the tables.
- Increase evidence budget for broad experiment mode to fit GPT-class 128k context windows while keeping ordinary questions compact.
- Mark references with evidence types such as `experiment_dossier`, `table_catalog`, and `table_pack` so citations remain truthful.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `paper-qa-evidence-grounding`: Paper Q&A SHALL choose retrieval/evidence strategy based on question intent and SHALL use an experiment evidence dossier for broad experiment/table analysis.

## Impact

- Affects `backend/app/services/paper_chunk_service.py`, current-paper Q&A context construction in `memory_service.py`, evidence metadata, and paper reader regression tests.
- No database migration and no new runtime dependency.
