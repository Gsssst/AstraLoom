## Context

The current paper-detail chat path builds a bounded evidence pack through `PaperChunkService`. Structured PDF parsing already normalizes parser-provided `formula` / `equation` blocks into evidence blocks, and the UI already tracks `formula_count`. However, retrieval does not currently elevate formula blocks when the user asks about formulas, equations, symbols, or a numbered section where formulas are important.

Mature paper-QA systems such as PaperQA-style pipelines keep answers grounded in retrievable evidence chunks and citations, while structured PDF tools such as Docling/Marker-style parsers preserve tables, figures, and formulas as typed blocks. The practical pattern for this codebase is to keep the current bounded evidence architecture and add a formula-specific evidence lane rather than injecting full PDFs or replacing parsers.

## Goals / Non-Goals

**Goals:**
- Detect formula/equation intent in Chinese and English queries.
- Include relevant structured `formula` evidence before generic top-k chunks.
- For numbered-section requests, merge formulas from the same requested section/page when available.
- Prompt the model to keep limitation language scoped and constructive.
- Avoid making unsupported claims about equations that were not retrieved.

**Non-Goals:**
- Replace PDF parsing with a new equation OCR system.
- Guarantee perfect formula extraction from image-only or malformed PDFs.
- Render formulas visually in the chat UI.
- Change frontend layout beyond existing evidence metadata display.

## Design

### Formula Intent Detection

Add a detector for formula-heavy requests using terms such as:

- Chinese: `公式`, `方程`, `符号`, `推导`, `Eq.`, `式`
- English: `formula`, `equation`, `eq.`, `loss`, `objective`, `derivation`, `alpha`, common LaTeX markers

This detection updates `PaperQuestionEvidencePlan` with `include_formula_evidence`, `formula_budget`, and targeted warnings when needed.

### Formula Evidence Lane

Structured candidates already include `source_type == "formula"`. Add a lane that:

- Ranks formula evidence by query token overlap, page/section proximity, and equation markers.
- For numbered-section requests, prefers formulas in or near the extracted numbered-section evidence page when page metadata exists.
- Merges selected formula evidence before ordinary text chunks while preserving the requested numbered-section range as the primary evidence.

### Scoped Limitation Language

Update paper Q&A prompt guidance:

- If evidence exists but formula blocks are incomplete, the model should say which formula/detail is unavailable.
- The answer should still explain the retrieved method/section using available evidence.
- Avoid headings or repeated phrasing that imply the algorithm or paper is broadly unreliable unless the evidence actually supports that judgment.

## Risks / Trade-offs

- Some formulas appear only as images and will remain unavailable without OCR/crop parsing.
- Formula blocks may be stored without section labels; page proximity is a useful but imperfect heuristic.
- Over-including formula evidence could crowd out text evidence, so the lane should be budgeted and merged with existing evidence limits.
