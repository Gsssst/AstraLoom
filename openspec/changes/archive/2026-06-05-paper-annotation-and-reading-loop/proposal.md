# Proposal: Paper Annotation and Reading Loop

## Why

The project now has paper discovery, push digests, reading status, and structured AI reading prompts. Two gaps remain:

1. PDF quote selection is temporary. Users can add selected text to the chat composer, but they cannot save quotes as reusable annotations or citations.
2. Digest recommendations can be ingested, but the action does not reliably connect to the reading queue. Users still have to jump between digest center and paper library to manage what to read next.

This change closes that loop: recommended papers can enter the reading queue, and important PDF passages can become saved annotations for later chat, notes, or reporting.

## What Changes

- Add persistent per-user paper annotations for selected PDF text.
- Show saved annotations in the paper detail page.
- Let users create an annotation from PDF selection, send it to chat, and delete it.
- Add reading-loop actions in the digest center:
  - Join paper library
  - Add to unread reading queue
  - Start reading
- Make digest feedback for "稍后阅读" ingest the paper and mark it as unread.
- Keep annotations personal to the current user.

## Out of Scope

- Rendering highlights directly on PDF pages across sessions.
- Multi-color PDF highlighter geometry.
- Public/shared annotations.
- Exporting annotations to Word or group meeting reports. This can be a follow-up.

## Risks

- Adding a new JSON field requires a small migration.
- The digest center may only have remote metadata before ingestion, so reading-loop actions must handle ingestion first.
- Annotation storage must preserve existing personal notes, tags, chat history, and read status.
