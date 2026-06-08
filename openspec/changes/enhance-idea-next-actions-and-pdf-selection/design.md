## Context

The research project page already computes proposal review scores, evidence counts, experiment completeness, validation entry points, code project generation, Copilot, timeline, and writing actions. These controls are distributed across cards, tabs, modals, and the proposal board. Similar GitHub research-agent projects commonly make the next step explicit by converting research artifacts into executable plans or checkpoints. The paper reader already supports selectable text and quote capture, but default PDF text-layer selection is visually dense when a multi-line passage is selected.

## Goals / Non-Goals

**Goals:**

- Add a compact next-action panel inside each proposal detail so users can immediately choose the most useful follow-up.
- Derive next actions from existing client-side proposal metadata and existing handlers instead of adding backend state.
- Improve PDF text selection appearance with CSS that reduces opacity, adds line spacing, and avoids a solid merged block.
- Keep the current quote-card behavior and PDF text selection behavior unchanged.

**Non-Goals:**

- Add a new AI endpoint or persist action recommendations in the database.
- Replace the existing proposal board.
- Rewrite the PDF viewer or annotation model.

## Decisions

- Use deterministic client-side action inference.
  The page already has enough state to suggest useful next steps without waiting on a model. This keeps the feature fast and avoids another model-cost surface.

- Present actions as a small panel in `renderProposal`.
  Users evaluate proposals inside the expanded proposal card, so the follow-up choices should sit next to hypothesis, evidence, review, and experiment information rather than only in a separate board tab.

- Use existing handlers for actions.
  Buttons will call existing flows such as `openCopilot`, `openTimeline`, `handleValidateIdea`, `openExperiment`, `handleGenerateCodeProject`, and writing handoff helpers where available.

- Refine PDF selection through CSS only.
  Browser selection pseudo-elements and PDF text-layer spans can be tuned without changing selection capture logic.

## Risks / Trade-offs

- Client-side action inference can be imperfect. Mitigation: show multiple clearly labeled actions rather than a single forced path.
- More buttons could clutter proposal cards. Mitigation: group them in a compact panel with concise rationale and bounded action count.
- PDF selection styling is browser-dependent. Mitigation: use standard `::selection` styling plus PDF text-layer spacing hooks and keep the underlying selection behavior intact.
