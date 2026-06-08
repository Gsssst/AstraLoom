## Why

Paper reading already supports PDF text selection, AI chat, notes, and saved annotations, but the current selection flow is too implicit: selecting PDF text immediately moves it into the chat composer, while non-PDF text uses a separate small popup. A contextual action menu makes selection feel deliberate and connects reading, asking, copying, notes, and annotations from one compact interaction.

## What Changes

- Add a unified selection action menu for paper detail text and PDF selections.
- Let users choose actions after selecting text: ask AI, explain, save as annotation, copy, or append to notes.
- Preserve the existing quote card, paper chat stream, annotation API, and personal notes workflow.
- Keep the interaction lightweight and responsive on mobile by moving to the relevant panel after an action.

## Capabilities

### New Capabilities

### Modified Capabilities
- `paper-reader-grounded-interaction`: selected paper/PDF text exposes contextual actions instead of only auto-inserting into the composer.

## Impact

- Frontend paper detail page selection handling and chat composer behavior.
- PDF viewer selection callback shape.
- Responsive styling and contract tests.
- No backend schema, API, or dependency changes.
