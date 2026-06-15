## Context

The product plan calls for Codex / Claude Code style tool ability. Mature references point to the same pattern: GPT Researcher uses planner/executor/source aggregation, STORM structures research as staged source curation, and PaperQA2 separates retrieval, ranking, and evidence-grounded answering. The first useful slice for this project is not arbitrary code execution; it is a transparent tool trace for the research actions the app already performs.

## Goals / Non-Goals

**Goals:**
- Introduce a typed `tool_trace` payload in chat stream metadata.
- Show tool steps with status, short summary, counts, and optional details.
- Connect Research Scout to the trace: parse intent, search scholarly sources, evaluate candidates, rank recommendations, and expose action tools.
- Keep side effects explicit and user-confirmed.
- Keep implementation small enough to ship before adding the full Skill system.

**Non-Goals:**
- Arbitrary model-initiated tool execution.
- Background job orchestration.
- New persistence tables for traces.
- Full Word/PPT/PDF extraction tools; those come in Phase 3.
- Skill registry or marketplace; that comes in Phase 4.

## Decisions

1. **Trace is metadata, not a database model.**
   - Store trace steps in streamed metadata next to `research_scout`.
   - Rationale: this keeps the first slice simple and avoids migrations while we learn the UI shape.

2. **Tool names are explicit and typed.**
   - Use a small registry: `parse_intent`, `search_papers`, `evaluate_papers`, `rank_recommendations`, `import_paper`, `add_to_folder`, `add_to_project`.
   - Rationale: this creates a stable UI/API contract without pretending every future tool exists yet.

3. **Side-effect tools are available, not auto-run.**
   - Import/add tools appear as `waiting` or `available` trace steps and map to existing card buttons.
   - Rationale: user confirmation remains required for library mutations.

4. **Research Scout drives the first trace.**
   - The backend already has deterministic phases; trace steps can be derived without a new agent runtime.
   - Rationale: visible progress can ship now, while a later phase can replace internals with a richer executor.

## Risks / Trade-offs

- **Trace may look fake if too generic** -> include concrete counts, providers, and candidate/evaluation summaries.
- **Too much trace detail can clutter chat** -> render a compact panel with concise status chips.
- **Future tools need persistence** -> defer until traces need replay/audit outside the current chat message.
