## Context

The chat toolbar has grown through several iterations and now repeats status and controls in the same horizontal area. On typical desktop widths, the title competes with the model badge, capability chips, retrieval label, mode toggles, depth selector, export button, and search input.

The research project page already treats recommended papers as secondary content, but the current frontend waits for that request inside the same `Promise.all` that controls the full-page loading spinner. The recommendation endpoint can be slow because it performs LLM-assisted query/entity generation, semantic retrieval, and external paper search.

## Goals / Non-Goals

**Goals:**
- Keep the chat toolbar visually calm while preserving all existing actions.
- Make primary chat mode controls easy to scan and move diagnostic status into a compact affordance.
- Let the research project page render once core project data is available.
- Load related paper recommendations independently with a local loading indicator.

**Non-Goals:**
- Replace Ant Design components or introduce a new UI library.
- Change chat request payloads, model routing, RAG behavior, or export format.
- Rebuild the research recommendation backend in this change.
- Change workbench generation semantics.

## Decisions

- Collapse detailed chat model/capability status into a compact status popover.
  - Rationale: users need the detail occasionally, but it should not consume primary toolbar width.
  - Alternative considered: hide status completely; rejected because model visibility and capability debugging are useful.
- Keep only high-frequency controls in the primary toolbar: knowledge-base toggle, web toggle, depth selector, and stop/export/more actions.
  - Rationale: this matches repeated chat use while keeping secondary actions discoverable.
- Move conversation search and clear conversation into the overflow menu.
  - Rationale: both are useful but not required for every turn.
- Split research project page loading into core and secondary requests.
  - Rationale: core workbench content should become interactive even if recommendation generation is slow.
- Keep using the existing recommended-papers endpoint for now.
  - Rationale: changing the backend selection strategy is a larger behavior change; the immediate pain is full-page blocking.

## Risks / Trade-offs

- [Risk] Moving search into a menu can make it slightly less obvious.
  → Mitigation: the overflow menu is kept in the toolbar with a clear icon and label.
- [Risk] Related papers may appear after the page has already rendered.
  → Mitigation: the related-papers card keeps its own loading state and empty copy.
- [Risk] Existing tests expect old class names.
  → Mitigation: preserve meaningful class names and update contract tests to cover the new compact structure.
