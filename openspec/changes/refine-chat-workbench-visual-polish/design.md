## Context

The chat page now supports normal conversation, Research Scout, RAG, web search, attachments, streaming status, a collapsible session rail, and a large bottom composer. The current styling overuses pill shapes, purple accents, glossy gradients, and heavy floating shadows. This makes the page feel less like a research workbench and less ready for the next phase of tool execution traces.

Open-source and product references inform the direction:
- Open WebUI keeps model, knowledge, and tool controls available but treats them as infrastructure around the chat stream.
- LobeChat uses modern spacing and agent affordances without letting every control compete for attention.
- Dify emphasizes workflow/tool traces, which need a neutral canvas and clear hierarchy rather than decorative surfaces.

## Goals / Non-Goals

**Goals:**
- Make the chat workspace feel calmer, sharper, and more professional.
- Preserve all current chat functions and Research Scout actions.
- Keep the desktop sidebar compact by default while making the expanded state feel like a real panel.
- Make the composer visually grounded at the bottom with restrained borders, shadows, and action hierarchy.
- Improve message, reference, and toolbar readability on desktop and mobile.

**Non-Goals:**
- Rebuild the chat page architecture.
- Change assistant behavior, stream payloads, backend APIs, or database models.
- Add Phase 2 tool execution traces in this change.
- Introduce a new design system dependency.

## Decisions

1. **Use a neutral workbench palette with a single blue accent.**
   - Rationale: the page currently reads as purple-heavy and glossy. A neutral surface with blue action accents is closer to research/product tooling.
   - Alternative considered: keep the purple gradient brand style. Rejected for the chat workbench because it amplifies the "plastic" feel.

2. **Reduce radius and shadow intensity across infrastructure surfaces.**
   - Rationale: oversized rounded cards and large shadows make the composer and messages feel like floating decorations.
   - Alternative considered: only tweak colors. Rejected because the shape language is a major part of the perceived quality issue.

3. **Keep message bubbles, but make assistant answers more document-like.**
   - Rationale: user messages can remain compact prompts; assistant answers should read as artifacts with references and cards attached.
   - Alternative considered: remove all bubbles. Rejected because the existing interaction model and action placement already depend on message rows.

4. **Turn toolbar controls into compact segmented infrastructure.**
   - Rationale: mode, knowledge base, web, status, search, and overflow controls should be available without making the top bar visually busy.
   - Alternative considered: move controls into a drawer. Rejected because power users need these toggles visible.

## Risks / Trade-offs

- **Risk: UI polish accidentally hides controls** → Keep every existing control in the DOM and add contract tests for key classes/text.
- **Risk: Reduced color makes active states unclear** → Use consistent border/background/icon states for active mode and retrieval controls.
- **Risk: Composer becomes too dense on mobile** → Add mobile-specific wrapping and hide secondary runtime text when space is tight.
- **Risk: Visual changes regress bottom alignment** → Reuse the existing chat workspace/composer structure and verify with build plus page smoke checks.
