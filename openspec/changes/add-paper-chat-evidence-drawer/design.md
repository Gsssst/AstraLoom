## Context

The paper-detail chat currently renders reference metadata inline below assistant answers. It already collapses reference content, but detailed inspection still lives inside the message flow. For answers involving many evidence types, especially table/visual evidence and web sources, this can consume vertical space and make the user inspect mixed evidence without type grouping.

## Goals / Non-Goals

**Goals:**
- Keep the chat message compact by default.
- Let users open a detailed evidence drawer per assistant answer.
- Categorize references into meaningful groups.
- Reuse existing click handlers to jump to PDF pages or open external URLs.
- Preserve current evidence confidence summary.

**Non-Goals:**
- Changing retrieval, evidence planning, or backend reference payloads.
- Rendering full image previews for table references.
- Persisting drawer state in chat history.

## Decisions

- Implement categorization client-side from existing `PaperChatReference` metadata.
  - `paper_text`: current-paper textual evidence.
  - `table`: table, visual table, table pack/catalog, or table caption evidence.
  - `visual`: visual/OCR/figure evidence that is not table-like.
  - `web`: web search references.
  - `related`: related-paper or other library references.
- Use an Ant Design `Drawer` controlled by page state.
  - The inline reference panel keeps a compact confidence summary and a button to open the drawer.
  - The drawer shows tabs or grouped sections with counts.
- Keep navigation centralized.
  - Drawer items call the existing `handleEvidenceReferenceClick` function so current PDF/web behavior remains unchanged.

## Risks / Trade-offs

- [Risk] Reference metadata can be incomplete. → Fall back to related/other categories and show available title/snippet.
- [Risk] Drawer can become dense for long answers. → Group evidence and cap snippets visually through CSS.
- [Risk] Duplicate inline and drawer controls can confuse users. → Keep inline area as summary plus a single clear "查看证据" action.
