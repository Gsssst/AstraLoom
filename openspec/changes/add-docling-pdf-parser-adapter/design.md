## Context

The advanced parser interface supports generic command execution, but a first-class adapter makes it easier to enable one proven parser. Docling's public examples use `DocumentConverter().convert(source)` and expose document exports such as Markdown; its document model also contains typed collections such as texts, tables, pictures, groups, and pages depending on version.

## Goals / Non-Goals

**Goals:**
- Add an optional `docling` backend value.
- Use Docling through dynamic import so the app does not require the package at startup.
- Convert Docling output into the existing structured extraction format.
- Preserve HuggingFace mirror/cache settings before Docling conversion.
- Fall back to lightweight extraction if Docling is missing or conversion fails.

**Non-Goals:**
- Add Docling to `requirements.txt`.
- Configure Docling OCR/VLM pipeline options in this iteration.
- Guarantee every Docling internal object shape across all versions.
- Replace the generic command backend.

## Decisions

1. Use dynamic import of `docling.document_converter.DocumentConverter`.
   - Rationale: deployments that install Docling get the adapter; deployments that do not install it still run normally.
   - Alternative considered: add Docling to backend requirements. Rejected because it can bring large optional model/runtime dependencies.

2. Normalize from several Docling shapes.
   - Rationale: Docling versions expose rich objects; tests should not depend on a single exact object class. The adapter will prefer `export_to_dict()` when available, use `export_to_markdown()` for whole-document evidence, and inspect common object collections.
   - Alternative considered: only consume Markdown. Rejected because typed objects give better evidence labels and page hints.

3. Treat Docling failures as parser failures, not user-facing errors.
   - Rationale: paper Q&A should remain available through lightweight parsing if the optional parser is unavailable.

## Risks / Trade-offs

- [Risk] Docling object schema changes. -> Use defensive attribute/dict extraction and keep command backend as an escape hatch.
- [Risk] Docling conversion can be slow. -> Existing structured parsing runs off the event loop and still falls back on failure.
- [Risk] Docling may use HuggingFace-hosted models. -> Apply runtime mirror/cache environment before constructing `DocumentConverter`.
