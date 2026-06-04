## Context

The paper detail page is intended to support close reading and grounded AI discussion side by side. Today, the AI panel can grow with each response and the PDF is loaded through an iframe. The iframe isolates its text selection from the application. The backend builds paper context from paragraph-sized chunks and BM25 scores, but it treats a direct request for a paper section like any other keyword query.

The interaction direction is informed by three open-source projects:

- Google PAIR's Lumi connects highlighted document evidence with AI questions and citations.
- Open Paper keeps reading, annotation, notes, and AI chat in a parallel workspace and exposes an inline menu for PDF text selection.
- PaperQA2 gathers evidence candidates before consolidating the context used for an answer.

This change adapts those patterns to the existing application without importing another paper assistant stack.

## Goals / Non-Goals

**Goals:**

- Preserve a stable PDF reading area while chat responses accumulate.
- Allow PDF text selection to become explicit quoted question context.
- Improve named-section questions such as requests to explain the introduction.
- Keep document-wide retrieval available for ordinary questions.

**Non-Goals:**

- Replacing the existing LLM provider or streaming protocol.
- Introducing vector databases, embedding jobs, or a full agentic research pipeline.
- Adding persistent PDF annotations or cross-device highlight synchronization.

## Decisions

### Reuse the existing text-layer PDF reader

The detail page will use the repository's existing `react-pdf` viewer instead of an iframe. Its text layer makes browser text selection observable by the application. The viewer will pass selected text and its page number to the page composer and size the rendered page from its container width.

The top-level `pdfjs-dist` dependency will be pinned to the exact version used by `react-pdf`. The PDF.js API and worker must share a version; allowing the direct dependency to resolve to a newer major version causes the worker handshake to fail before a document can be displayed.

Selected text will be stored separately from the editable question draft and rendered as a removable quote card above the editor. When a question is submitted, the quote is merged into the model-facing question while the visible user message preserves a compact quote preview. The editor will auto-grow within a bounded row range so longer prompts remain comfortable without taking over the message viewport.

Alternative considered: keeping the iframe and attempting to read its selection. That is brittle because embedded PDF viewers are browser-controlled documents and may be isolated from application event handling.

### Constrain the workspace with nested flex overflow rules

The page, body, panels, chat card, and message list will explicitly opt into `min-height: 0` and internal overflow. Only the chat message list and PDF canvas container will scroll. The composer and paper chat controls remain fixed.

Alternative considered: limiting each response height. That would hide content and still leave the workspace ownership of scrolling unclear.

### Route section requests before generic ranking

The retrieval service will recognize common English and Chinese section aliases, split full text around section headings, and search only the requested section when it is found. If the requested section cannot be located, the existing document-wide chunk ranking remains the fallback.

This is a lightweight adaptation of candidate evidence narrowing: first choose the likely evidence scope, then apply the existing scorer. It avoids introducing embeddings while addressing direct section questions.

Alternative considered: only increasing `top_k`. That adds unrelated text and does not reliably surface the named section.

### Load full text through installed parsers and bound reasoning time

Paper detail preload and paper questions will share an in-flight full-text task keyed by paper identity. PDF extraction will use the already-installed `pdfplumber` parser first and retain `fitz` only as an optional fallback. A question may wait briefly for extraction, but cancellation of that foreground wait will not cancel persistence of the shared background task.

Paper thinking streams will have a bounded primary duration. If the model spends the whole window on reasoning without producing visible answer text, paper chat will switch to the existing stable answer mode. This protects responsiveness while preserving thinking output when it completes normally.

## Risks / Trade-offs

- [Risk] PDF text extraction may omit or distort headings in some source files. -> Mitigation: preserve document-wide retrieval as a fallback.
- [Risk] Switching from the browser PDF viewer to `react-pdf` initially renders one page at a time. -> Mitigation: retain page navigation and responsive width while keeping the implementation focused.
- [Risk] Text selection can overwrite an unfinished question. -> Mitigation: append a clearly labeled page quote when the composer already contains content.
- [Risk] Section aliases can accidentally match broad terms. -> Mitigation: prefer explicit academic section names and normalize only heading-like lines.

## Migration Plan

Deploy the frontend and backend changes together. No data migration is required. Rolling back restores the iframe and generic retrieval without affecting persisted paper content or conversations.

## Open Questions

- Persistent PDF annotations and multi-highlight question composition can be evaluated as a later capability.
