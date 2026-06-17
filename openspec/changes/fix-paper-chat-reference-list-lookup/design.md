## Context

Current paper Q&A evidence routing has special lanes for sections, formulas, tables, datasets, experiments, novelty, and visual evidence. It does not have a bibliography lane. A question about `Reference [1]` therefore uses BM25 over generic chunks, which can rank the first visible in-text citation above the actual reference-list entry.

## Goals / Non-Goals

**Goals:**
- Recognize reference-list lookup intent before generic retrieval.
- Extract reference entries from common `References`, `Bibliography`, and Chinese `参考文献` sections.
- Prefer exact requested reference numbers such as `[1]`, `Reference 1`, or `第一篇参考文献`.

**Non-Goals:**
- Build a full citation graph or resolve references to external metadata.
- Rewrite stored paper metadata or add a database field.
- Use an LLM to infer missing bibliography entries.

## Decisions

- Implement deterministic extraction in `PaperChunkService`. The evidence router is already the single point that decides what gets sent to the model.
- Use source priority `page_texts -> full_text -> structured_blocks`, because page text tends to preserve the References section in PDF order and retains page numbers for UI references.
- Parse numbered entries with common markers (`[1]`, `1.`, `[12]`) and include a compact reference-list catalog when no specific number is requested.
- Return a warning when a specific reference number is requested but the list cannot be located, so the model can say exactly what is missing.

## Risks / Trade-offs

- [Risk] Some PDFs split one bibliography entry across lines or pages. -> Keep continuation lines until the next numbered entry and search across page text plus full text.
- [Risk] Numeric body text could be mistaken for bibliography entries. -> Only parse entries inside a detected reference-list section.
- [Risk] Some papers use unnumbered author-year references. -> This change focuses on numbered references because the reported failure concerns `Reference [1]`; author-year lookup can be added later.
