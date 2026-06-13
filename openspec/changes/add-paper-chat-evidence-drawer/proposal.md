## Why

Paper-detail AI answers already return references, but the inline citation area can still be hard to inspect when many evidence items are present. Research chat products such as RAGFlow, Open WebUI, AnythingLLM, and Quivr treat traceable sources as a core RAG affordance, so paper answers need a compact way to inspect evidence by type without taking over the chat message.

## What Changes

- Add a paper-chat evidence drawer opened from each assistant answer.
- Group answer references into evidence categories such as current-paper text, tables, visual/OCR evidence, web sources, and related papers.
- Preserve existing inline collapsed reference summary while moving detailed evidence inspection into the drawer.
- Keep click behavior for PDF evidence and external sources.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `paper-detail-chat-parity`: Paper-detail AI Q&A exposes answer references through a categorized evidence drawer.

## Impact

- Affects `PaperDetailPage.tsx`, paper-chat reference rendering styles, and frontend contract tests.
- No backend API or database changes are required.
