## Context

The current Research Idea Workbench can stop at `gap_review`, let users select or block Gap Map items, and continue proposal generation with generation constraints. The missing loop is quality correction: users can see when a gap is too broad, weakly evidenced, already known, or simply misaligned, but that judgment is not persisted or reused.

Similar open-source research ideation systems point toward iterative artifact refinement rather than one-shot generation:
- Open Coscientist uses a staged generate/review/rank/evolve workflow over research hypotheses.
- Open AI Co-Scientist reimplementations expose reflection, ranking, evolution, and proximity checks as explicit stages.
- HypoGeniC/HypoRefine combines data or literature with refinement loops before returning hypotheses.
- Research canvas projects such as Open Research ANA emphasize human-in-the-loop continuation and approval.

This change treats each Gap Map item as a first-class intermediate artifact that can receive user edits and feedback before proposal generation.

## Goals / Non-Goals

**Goals:**
- Let project editors update per-gap text fields, quality rating, labels, notes, and evidence references.
- Let project editors refine one Gap Map item without rerunning evidence retrieval or the full idea pipeline.
- Show linked evidence for each gap directly in the Gap Map review UI.
- Include edited gaps and feedback summaries in candidate generation and tree-evolution prompts.
- Persist gap feedback in existing run JSON fields so refresh and continuation preserve user intent.

**Non-Goals:**
- Adding new database tables or migrations.
- Multi-user voting or threaded comments on gaps.
- Full background job orchestration for gap refinement.
- Replacing the current end-to-end generation or Gap Map preview flows.

## Decisions

### Store feedback in existing Gap Map JSON

Each gap can carry:
- `user_feedback.rating`: `strong`, `promising`, `weak`, or `reject`
- `user_feedback.labels`: constrained tags such as `valuable`, `too_broad`, `evidence_weak`, `already_done`, `misaligned`
- `user_feedback.note`: free-form user note
- `refinement`: metadata describing the last single-gap refinement

The frontend edits the visible gap fields directly; the backend normalizes the payload and writes the mutated `run.gap_map`.

### Use index-based mutation with title fallback in UI

The API uses `gap_index` from the path because gap titles are editable and not stable identifiers. The frontend still renders titles normally and keeps selection by title for the existing continue flow. After edits/refinement, the selection state is reinitialized from the returned run.

### Single-gap refinement uses current evidence and feedback

The refine endpoint builds a focused prompt from:
- the project brief
- the current gap item
- evidence items linked by `evidence_ids`
- current `user_feedback`
- the user's refine note

If the model returns invalid output, deterministic fallback rewrites the gap into a narrower, evidence-oriented form and preserves the feedback metadata.

### Candidate generation receives feedback summary

`generation_context_from_run` will include `gap_feedback` derived from the current Gap Map. Prompt formatting will include edited text, rating, labels, and notes. Fallback candidates will avoid rejected gaps when possible and reflect low-quality feedback in approach wording.

## Risks / Trade-offs

- [Risk] Users can over-edit a gap into something no longer supported by evidence. → Keep evidence IDs visible and persist weak-evidence labels for generation context.
- [Risk] Index-based mutation can target the wrong gap if concurrent changes reorder the list. → The workbench currently has a single-user editing flow per run; no collaborative reordering is introduced.
- [Risk] More controls could clutter the Gap tab. → Keep editing collapsed into a compact per-gap panel and show evidence snippets only inside the gap card.
- [Risk] LLM refinement may produce broad or malformed gaps. → Normalize with existing gap schema and use deterministic fallback.
