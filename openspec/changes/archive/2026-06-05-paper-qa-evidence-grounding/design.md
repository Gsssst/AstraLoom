## Context

The paper Q&A flow already tries to load full text and retrieve relevant chunks. However, chunks are passed only as raw prompt text. The frontend receives related-paper references but not current-paper evidence. This means users cannot verify which page/fragment supports an answer.

## Goals / Non-Goals

**Goals:**
- Bind paper Q&A context to structured evidence snippets.
- Prefer explicitly requested sections.
- Expose page/snippet references in stream metadata.
- Allow clicking evidence references to jump the PDF viewer page.
- Surface evidence coverage and evidence-insufficient warnings.

**Non-Goals:**
- Exact PDF coordinate highlighting.
- Persisting evidence references in a separate database table.
- Full citation validation of generated prose after model output.

## Decisions

### Preserve existing context builder compatibility

Add `build_paper_context_with_evidence()` while keeping `build_paper_context()` as a wrapper. This limits blast radius for existing callers.

### Page-aware extraction is best-effort

When a cached PDF path is available, extract page texts and build evidence chunks per page. If page texts are unavailable, fall back to full-text chunks without page numbers. References label page as best-effort evidence rather than exact visual coordinates.

### Prompt evidence discipline explicitly

The paper Q&A system prompt requires each major conclusion to be supported by evidence references, and to say "当前论文内容不足" when evidence is missing.

### Frontend PDF jumping uses page navigation

PDFViewer receives an optional target page. Clicking an evidence reference sets that target page and opens/shows the PDF panel.

## Risks / Trade-offs

- [Page numbers can be approximate when text extraction differs from visual layout] -> Surface page references as evidence navigation, not exact highlighting.
- [Parsing page text on demand can add latency] -> Only use cached PDF paths and fall back cleanly.
- [Model may still omit citations] -> Prompt discipline plus visible evidence coverage improves user verification; post-generation citation enforcement can be a later phase.

## Migration Plan

1. Add evidence chunk models and page-aware retrieval helpers.
2. Add context builder with evidence metadata and stricter grounding prompt.
3. Include evidence references in paper Q&A metadata.
4. Add frontend evidence reference rendering and PDF page jump.
5. Add regression tests and run validation.
