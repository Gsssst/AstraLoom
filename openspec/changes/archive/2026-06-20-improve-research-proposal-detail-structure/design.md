## Context

The workbench already follows a mature research-agent pipeline: evidence collection, Gap Map extraction, multi-path candidate generation, deduplication, review, novelty checks, and final proposal persistence. The weak point is the shape of the proposal itself. The current selected idea stores `description = gap + hypothesis`, `approach = technical sketch`, and `experiment_plan = minimum_experiment`, so the UI has to display a compact paragraph even when users need a plan they can inspect.

Reference patterns from mature projects:
- AI-Scientist-style idea templates separate title, experiment, feasibility, and novelty so generated ideas are executable.
- STORM-style writing first builds an outline before long-form content, improving readability and coverage.
- SciPIP-style ideation keeps evidence and generation paths inspectable so users can trace why a proposal exists.

## Goals / Non-Goals

**Goals:**
- Make newly generated proposals more detailed and easier to inspect.
- Keep generated content structured enough for the frontend, writing handoff, and experiment planning.
- Preserve compatibility with old proposals and existing API response shapes.

**Non-Goals:**
- Rebuilding the entire candidate generation pipeline.
- Adding a new database column or migration.
- Rewriting score/ranking algorithms.
- Changing how many evidence papers are collected.

## Decisions

1. **Store `proposal_outline` inside `review_json`.**
   - Rationale: `review_json` already carries proposal-level metadata and can evolve without a migration.
   - Alternative considered: a dedicated column. That is cleaner long term but unnecessary for this scoped iteration.

2. **Normalize outline server-side with deterministic fallbacks.**
   - Rationale: the LLM may omit fields. The UI should still get a predictable object.
   - Alternative considered: frontend parsing from free text. That would keep the backend unchanged but does not improve downstream writing/experiment reuse.

3. **Preserve legacy text fields.**
   - Rationale: existing cards, sorting, validation, writing, and code generation depend on `description`, `approach`, `hypothesis`, and `experiment_plan`.
   - Alternative considered: replace text fields entirely. Too risky and unnecessary.

4. **Render sectioned UI only when outline exists.**
   - Rationale: old ideas remain readable without data migration.
   - Alternative considered: always render synthetic sections from text. That can mislead users by implying more structure than exists.

## Risks / Trade-offs

- Longer prompts may increase token use -> add bounded fields and truncate normalized strings.
- LLM may still generate vague content -> add stricter prompt requirements and fallback outline construction.
- More UI sections may feel dense -> use compact subsections, bullets, and existing evidence/risk panels rather than another nested card-heavy layout.
