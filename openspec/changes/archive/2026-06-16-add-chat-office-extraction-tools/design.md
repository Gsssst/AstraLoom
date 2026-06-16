## Context

The shared chat attachment hook uploads files to `/chat-sessions/extract-file`, and the backend currently extracts images, PDFs, and plain text. Office files are common research inputs: Word drafts, reviewer notes, paper summaries, lab meeting slides, and experiment planning decks. The project already depends on `python-docx`; PowerPoint support needs the lightweight `python-pptx` parser.

Mature document-agent systems such as Unstructured and LangChain document loaders treat office files as structured document chunks rather than opaque binary uploads. This change follows that pattern locally without bringing in a heavy ETL stack.

## Goals / Non-Goals

**Goals:**

- Extract `.docx` text into bounded sections including paragraphs, headings, and tables.
- Extract `.pptx` text into bounded slide blocks with slide numbers, titles, and text items.
- Reuse the same extraction helper from `/extract-file`, legacy chat upload, and registered read-only tools.
- Register `extract_docx` and `extract_pptx` as safe read-only tools for planner visibility.
- Keep frontend attachment acceptance in sync with backend capabilities.

**Non-Goals:**

- Full fidelity Office rendering.
- `.doc` / `.ppt` binary legacy parsing beyond clear unsupported guidance.
- OCR of images embedded inside Office files.
- Parsing comments, tracked changes, speaker notes, charts, or SmartArt in this first slice.
- Persisting Office files.

## Decisions

### Decision: Add a small extraction service

Create a focused backend helper module for Office extraction so route handlers and tools call the same code path.

Rationale: keeping extraction out of `chat_sessions.py` prevents the route file from growing further and makes tests easier.

### Decision: Use `python-docx` and `python-pptx`

DOCX uses the existing `python-docx` dependency. PPTX uses `python-pptx` because it is a small direct parser for slide shapes and text frames.

Rationale: Unstructured and textract are broader, heavier dependencies. The current need is bounded text extraction, not a full document ETL pipeline.

### Decision: Bound extracted content

Extraction helpers return structured text capped to the same chat upload safety envelope, with per-file summaries and text length metadata.

Rationale: chat context must remain predictable and uploads already have a 50MB file size ceiling.

### Decision: Legacy Office formats are explicit errors

`.doc` and `.ppt` are accepted by the picker for user ergonomics, but the backend returns an actionable unsupported-format error unless the file can be decoded as plain text.

Rationale: parsing old binary Office files reliably would require heavier dependencies or external conversion.

## Risks / Trade-offs

- **PPTX charts and images are not extracted** -> Return slide text only and clearly scope this as text extraction.
- **DOCX tables can be verbose** -> Cap rows/cells through global extracted text limits.
- **Users may upload `.doc` / `.ppt`** -> Return a clear error requesting `.docx` / `.pptx`.
- **Dependency mismatch on deploy** -> Add `python-pptx` to `backend/requirements.txt` and cover import paths in tests.
