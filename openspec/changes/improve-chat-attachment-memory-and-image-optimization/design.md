## Context

The main chat and paper-detail chat now share temporary attachment extraction through `/chat-sessions/extract-file`. PDF attachments contribute extracted text and image attachments contribute data URLs to the next model request. This is good for one-off questions but weak for normal research usage, where users upload a figure or supplementary PDF and then ask several follow-up questions.

Large uploaded images are also accepted because the file limit is 50MB. Sending those images unchanged as base64 JSON can inflate payload size and produce avoidable latency or upstream request failures.

## Goals / Non-Goals

**Goals:**
- Preserve temporary attachment context across follow-up turns in the current frontend chat surface.
- Let users remove remembered attachments before later turns.
- Reuse the same behavior in main chat and paper-detail chat.
- Optimize image data URLs for model submission by resizing/re-encoding client-side.
- Keep the accepted file limit at 50MB.

**Non-Goals:**
- Persisting temporary attachments in the database or paper library.
- Changing paper ingestion, structured parsing, or visual evidence extraction.
- Adding a new backend upload endpoint.
- Building a full attachment manager outside the current chat surfaces.

## Decisions

- Store remembered attachments in the shared `useChatAttachments` hook.
  - Current-turn attachments remain editable before send.
  - On successful send, ready attachments move into remembered state instead of disappearing from all future turns.
  - Follow-up sends include remembered PDF text and remembered image payloads unless removed.
- Keep remembered attachments frontend-local.
  - This avoids changing chat history persistence and avoids treating temporary files as library documents.
  - Reloading the page clears temporary attachment memory.
- Deduplicate attachment context by hook-level IDs.
  - Current-turn attachments and remembered attachments can be merged for send without repeating the same file after it moves to memory.
- Optimize images in the browser.
  - Use canvas resizing/re-encoding for image files before model submission.
  - Preserve the original filename/type for display while using an optimized data URL for model payloads.
  - If compression fails, fall back to the extracted data URL rather than blocking the user.
- Surface status in attachment chips.
  - Chips can show extracting, ready, remembered, optimized, or optimization fallback states using concise labels.

## Risks / Trade-offs

- [Risk] Frontend-local memory is lost on refresh. → This matches temporary attachment semantics and avoids accidental persistence.
- [Risk] Canvas cannot decode some image formats. → Keep fallback to original extracted data URL.
- [Risk] Multiple remembered images may still create large multimodal requests. → Keep the existing max attachment count and resize each image to a bounded model payload.
- [Risk] Remembered PDF text can make prompts too long. → Reuse the existing extracted text cap and combine context with clear section headers.
