## Context

The current chat composer uploads files to `/chat-sessions/extract-file` before sending. For images, that endpoint returns only a filename-based text prompt. `/send-stream` then calls `MemoryService.build_context()` with that text as `extra_context`, so the selected LLM never receives image bytes.

The configured OpenAI-compatible GPT endpoint has been verified to accept Chat Completions content parts with `{"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}`. DeepSeek is text-only for this project.

## Goals / Non-Goals

**Goals:**
- Let GPT-compatible chat see uploaded images in the same message as the user's prompt.
- Keep text/PDF attachment behavior intact.
- Avoid storing full base64 images in chat history.
- Provide a clear text-only fallback for DeepSeek.

**Non-Goals:**
- Add OCR for DeepSeek.
- Add permanent image asset storage.
- Support multi-turn image recall from history after the original request.

## Decisions

- Add an `attachments` field to the streaming chat request for image data URIs.
  - Rationale: the image is needed only during the current model call; the persisted user message can remain a readable filename/prompt.

- Build multimodal user message content at the API boundary only when the active provider is OpenAI-compatible.
  - Rationale: this keeps memory/history as text and limits multimodal payloads to providers that support them.

- For DeepSeek/text-only providers, append a clear system context explaining that image visual content is unavailable.
  - Rationale: this prevents misleading answers that imply the model saw the image.

## Risks / Trade-offs

- Base64 images increase request size and token/billing cost -> mitigation: preserve the 10MB upload limit and send images only for the current request.
- Some OpenAI-compatible endpoints may claim GPT support but reject images -> mitigation: API errors surface through the existing stream error path; the previously verified endpoint supports the format.
