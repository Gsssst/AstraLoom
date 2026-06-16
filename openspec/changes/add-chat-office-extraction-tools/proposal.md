## Why

Chat attachments currently handle images, PDFs, and plain text, but Word and PowerPoint files still fail or degrade to raw text decoding. Stage 2 needs reliable office-document extraction so the chat agent can inspect meeting notes, paper drafts, slides, and research materials as first-class evidence.

## What Changes

- Add reusable backend extraction helpers for `.docx` and `.pptx` files.
- Support Word extraction of paragraphs, headings, and tables as bounded structured text.
- Support PowerPoint extraction of per-slide titles and text boxes as bounded structured text.
- Register read-only generic chat tools `extract_docx` and `extract_pptx` for future agent use.
- Update `/chat-sessions/extract-file` and legacy chat upload handling to use the same office extraction path.
- Update the shared frontend attachment picker to accept `.docx`, `.doc`, `.pptx`, and `.ppt`.
- Add `python-pptx` as the lightweight backend dependency for PowerPoint parsing.

## Capabilities

### New Capabilities

### Modified Capabilities

- `chat-agent-tool-runtime`: The registered tool set expands with read-only office document extraction tools.
- `chat-retrieval-mode-coordination`: Chat attachments include Word and PowerPoint document extraction in the shared file workflow.

## Impact

- Backend file extraction logic in `backend/app/api/chat_sessions.py` or a helper service.
- Backend tool registry in `backend/app/services/chat_agent_tools.py`.
- Backend dependency list in `backend/requirements.txt`.
- Shared attachment hook in `frontend/src/hooks/useChatAttachments.ts`.
- Focused backend tests for `.docx` and `.pptx` extraction and frontend contract tests for accepted file types.
