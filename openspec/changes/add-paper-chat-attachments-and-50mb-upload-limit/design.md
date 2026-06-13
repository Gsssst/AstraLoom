## Context

The main chat page currently performs temporary file extraction client-side through `/chat-sessions/extract-file`, then sends extracted PDF text as `extra_context` and image files as model attachments. Paper-detail AI Q&A only accepts typed questions and selected PDF quotes, even though the same extraction workflow is useful when asking about an external paper, supplementary PDF, or figure.

Comparable open-source document chat systems such as Quivr, AnythingLLM, and RAGFlow treat uploaded documents as temporary or persisted context for chat. For this project, a temporary context path is the smallest compatible change because the user asked for paper-page chat capability, not paper-library ingestion.

## Goals / Non-Goals

**Goals:**
- Share attachment upload/extraction behavior between main chat and paper-detail chat.
- Raise the file size limit to 50MB for accepted PDF/image attachments.
- Let paper-detail AI Q&A include attachment text and images alongside the current paper context.
- Keep attachment chips removable and visible before sending.

**Non-Goals:**
- Persisting paper-detail attachments as library papers.
- Adding a new backend upload or storage endpoint.
- Changing OCR, visual evidence extraction, or paper ingestion workflows.

## Decisions

- Extract a reusable frontend hook for temporary chat attachments.
  - The hook keeps file size validation, extraction status, data URLs, text, and removal logic in one place.
  - Both main chat and paper-detail chat use the same 50MB limit.
- Keep backend request compatibility.
  - Main chat continues to send extracted PDF text as `extra_context` and image data URLs as `attachments`.
  - Paper-detail chat prepends extracted attachment text to the question context and sends image data URLs in an `attachments` request field if supported by the backend stream endpoint.
- Avoid importing uploaded files into the paper library.
  - These attachments are transient per question and cleared after send.

## Risks / Trade-offs

- [Risk] Very large PDFs can produce too much extracted text for a single prompt. → Reuse the current extraction endpoint behavior and only include extracted text available from that endpoint.
- [Risk] Paper-detail backend may ignore image attachments until it explicitly supports the request field. → Include image metadata in the user-visible context and request body without breaking current text-only handling.
- [Risk] Duplicate upload UI logic drifts again. → Centralize the logic in a shared hook and cover usage with tests.
