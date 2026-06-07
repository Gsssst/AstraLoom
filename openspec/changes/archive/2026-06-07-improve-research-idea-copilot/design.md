## Context

Saved Research Ideas already carry useful structured state: evidence metadata, review metadata, experiment plans, validation results, execution pack data, lineage, and evolution rationale. The existing `discuss_idea` method does not use most of that state; it sends a minimal prompt and stores a flat discussion log. The frontend exposes discussion inside each Proposal card, which makes longer idea iteration cramped and separates discussion from validation/evolution actions.

## Goals / Non-Goals

**Goals:**
- Make AI discussion aware of the idea's evidence, validation, execution readiness, lineage, and evolution history.
- Let users choose the discussion stance that matches the current work: mentor, skeptic, experiment designer, or writer.
- Return structured metadata that can drive UI affordances and subsequent evolution.
- Allow a user to create a new Proposal version from a discussion-derived focus without duplicating the existing evolution implementation.
- Present discussion as a focused Copilot panel with markdown and compact context status.

**Non-Goals:**
- Introduce autonomous multi-agent execution.
- Add a new model provider or change LLM selection.
- Persist a new normalized discussion table.
- Replace existing validation, execution pack, or lineage endpoints.

## Decisions

- **Use existing persisted JSON fields instead of a migration.** Discussion output can be stored in `discussion_log` as entries with optional metadata while preserving existing role/content entries. This avoids schema churn and keeps backwards compatibility.
- **Reuse validation and execution pack services as Copilot context.** The Copilot should not invent another evaluator when `ResearchIdeaWorkbenchService` already derives collision risk, checklist, writing readiness, and execution tasks.
- **Add mode and structured metadata at the API boundary.** The discussion response should include `reply`, `discussion_log`, `mode`, `context_summary`, `risks`, `next_actions`, `suggested_questions`, and `evolution_focus` so the frontend can render actions without brittle prompt parsing.
- **Route discussion-driven evolution through existing `evolve_idea`.** A dedicated endpoint can compose a focus from request text or latest Copilot metadata, then call the existing evolution path so lineage and parent preservation stay consistent.
- **Implement the UI as an in-page drawer/panel.** A drawer keeps Proposal cards scannable while giving longer conversations enough space. The panel can reuse the selected idea and existing project page state instead of introducing a route.

## Risks / Trade-offs

- Richer context may increase prompt size and latency -> keep context summaries bounded and include only recent discussion turns.
- Structured model output may be malformed -> parse JSON opportunistically and fall back to plain reply plus deterministic metadata from validation/execution context.
- Discussion logs can contain older unstructured entries -> frontend and backend must tolerate both legacy and structured log shapes.
- UI complexity could grow inside `ResearchProjectPage.tsx` -> keep helper renderers and state narrowly scoped in this change, leaving deeper component extraction for a later cleanup if needed.
