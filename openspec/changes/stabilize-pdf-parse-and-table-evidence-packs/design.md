## Context

Current behavior has two confirmed failures:

- Twilight has `full_text` but no `pdf_path`, while `uploads/arxiv-pdfs/2502.02770.pdf` is valid. `force_structured_pdf_reparse()` calls `ensure_full_text()`, but `ensure_full_text()` returns early when full text exists, so it never restores `pdf_path`.
- Paper Q&A currently requests `top_k=4` evidence snippets. Table-heavy questions often need a caption, table body, same-page explanatory text, and sometimes a baseline table. Four independent snippets are not enough, and isolated table rows can lack column meaning.

Related project patterns:

- RAGFlow exposes parser/chunk state and uses multiple retrieval signals before presenting references.
- Docling, MinerU, and Marker produce structured Markdown/JSON-like document units; tables are not treated as anonymous plain text chunks.

## Goals / Non-Goals

**Goals:**
- Recover missing local PDF paths for arXiv papers before structured parsing.
- Persist recovered `pdf_path` so future parsing and viewing are stable.
- Surface actionable parser health and parse error details.
- Use an adaptive evidence budget for current-paper Q&A.
- Retrieve table evidence as grouped packs: table, caption, same-page text, and metadata.

**Non-Goals:**
- Install Docling, MinerU, Marker, or any heavy parser dependency in this change.
- Build pixel-level visual table understanding.
- Replace the current BM25 retrieval stack with a vector database pipeline.

## Decisions

1. Add a PDF path resolver for arXiv papers.
   - Rationale: parsing should not fail when the cached PDF exists and only `paper.pdf_path` is missing.
   - Behavior: if `paper.pdf_path` is empty and `arxiv_id` exists, call the shared arXiv PDF cache resolver, update `paper.pdf_path`, and optionally persist through the provided DB/session.

2. Use parser health as operational metadata.
   - Rationale: "auto" is only useful if operators can see whether Docling or command parser is actually installed/configured.
   - Health fields: configured backend, supported backends, `pdfplumber` availability, `fitz` availability, `docling` availability, command parser configured, HuggingFace endpoint/cache settings.

3. Make table-like Q&A use larger but bounded evidence.
   - Rationale: more evidence is useful for tables only if it is structured and diverse.
   - Behavior: default current-paper evidence remains compact, while table-like questions reserve additional slots for table packs.
   - Constraint: selected table bodies must be preserved in full; prompt control comes from limiting the number of table packs and truncating only supplemental caption/body context.

4. Build evidence packs at retrieval time without changing metadata schema.
   - Rationale: stored blocks already contain `type`, `page`, `source`, text, and metadata; packing can be computed from candidates.
   - Packing rules: for a selected table, include table captions from the same page, same-page text chunks, and closely related table/baseline blocks when relevant.

5. Keep answer references truthful.
   - Rationale: the UI and model should know whether a snippet is a table, caption, text, or grouped table pack.
   - References keep source type, parser source, score, snippet, metadata, and PDF page.

## Risks / Trade-offs

- [Risk] Larger context increases prompt size. -> Cap grouped evidence by count and supplemental context length, while preserving selected table bodies in full.
- [Risk] Same-page text can be noisy. -> Include same-page text only as context around selected tables and keep diversity filtering.
- [Risk] Parser health can be mistaken for quality. -> Label it as availability/configuration, while table quality remains separate metadata.
