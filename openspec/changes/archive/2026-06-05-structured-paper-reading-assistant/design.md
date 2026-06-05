# Design: Structured Paper Reading Assistant

## Overview

The frontend will define a small set of paper reading templates. Each template contains:

- `key`
- `title`
- `description`
- `icon`
- `question`

The question is sent through the existing `handleAsk` flow in `PaperDetailPage`, so no backend data model or endpoint changes are required. The prompt text will explicitly request evidence-grounded answers and ask the model to say when the paper does not provide enough information.

## Frontend

### Shared Template Definition

Add `paperReadingTemplates` near the top of `PaperDetailPage.tsx`. The templates should use section names like `Introduction`, `Method`, and `Experiments` in the question text so the existing section-aware chunk retrieval can prioritize those sections.

### Submission Flow

Refactor the current `handleAsk` logic into a helper:

```ts
const submitPaperQuestion = async (rawQuestion?: string, displayQuestion?: string) => { ... }
```

`handleAsk` delegates to this helper with the current input state. Template buttons call it with a fixed template question and display title.

### Reading Assistant Panel

In the content panel, add a compact card below the paper metadata and before the abstract:

- Shows current reading status and context scope.
- Shows six template action buttons/cards.
- Disables template actions while `asking` is true.
- On mobile, switches to the chat panel after firing a template.

### Empty Chat Prompts

Replace or supplement the existing ad-hoc prompt list with the same template list so the chat panel and content panel provide consistent reading workflows.

## Backend

No endpoint changes are required. Existing paper chat already:

- Loads full text when possible.
- Performs chunk retrieval over full text.
- Detects requested sections through the paper chunk service.
- Streams thinking/content through the existing SSE protocol.

## Verification

- Frontend production build.
- Layout contract tests.
- Strict OpenSpec validation.
- Browser verification attempted where available.
