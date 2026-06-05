## Context

`_paper_brief()` intentionally truncates `abstract` to 500 characters for cards. The paper-summary modal currently reads the same field, so it cannot show more text than the card response contains.

## Goals / Non-Goals

**Goals:**

- Keep card previews concise.
- Include the complete available abstract in paper-card API responses.
- Use the complete field in the modal without breaking older responses.

**Non-Goals:**

- Fetch PDF full text.
- Replace the paper-detail page.

## Decisions

### Add `abstract_full` alongside the preview

The API will retain `abstract` as the 500-character preview and add optional `abstract_full`. The frontend modal will prefer `abstract_full` and fall back to `abstract`.

Alternative considered: remove truncation from `abstract`. Rejected because it changes the established preview field semantics and sends unclear payloads to other consumers.

## Risks / Trade-offs

- [Risk] Search responses are slightly larger. → Abstracts are bounded scholarly metadata and the card preview remains unchanged.

