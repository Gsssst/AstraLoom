## Context

The previous change added `proposal_outline`, which made proposals more structured but also increased visual density. The next step is not to add more parallel panels. It should make the primary proposal story stronger and move audit material behind disclosure controls.

Comparable systems suggest four useful patterns:

- AI-Scientist-style idea generation is useful because ideas are connected to executable experiment templates, but this product should not automatically run experiments in this change.
- STORM-style writing starts with an outline before expansion; selected proposals should therefore default to a compact brief before showing details.
- SciPIP-style ideation combines literature evidence with model reasoning; deepening should use evidence metadata plus the model's own critique rather than only reformatting existing text.
- Scideator-style facets separate problem, mechanism, evaluation, limitation, and transferable insight; deepening should explicitly improve these facets.

## Goals

- Make a proposal readable in under one minute from a compact brief.
- Let the user deepen one selected idea without starting a full new generation run.
- Preserve existing validation, discussion, code generation, writing handoff, and review metadata.
- Avoid a migration by storing new structured fields under `review_json`.

## Non-Goals

- Do not build autonomous experiment execution.
- Do not redesign the whole research project page.
- Do not remove existing review data or proposal actions.
- Do not require existing proposals to be backfilled.

## Data Model

Use `ResearchIdea.review_json` for the new fields:

- `idea_brief`: compact object with:
  - `research_question`
  - `key_insight`
  - `core_hypothesis`
  - `mechanism`
  - `minimum_experiment`
  - `failure_condition`
  - `next_actions`
- `deepening`: latest focused deepening result with:
  - `version`
  - `focus`
  - `critique`
  - `improved_brief`
  - `evidence_facets`
  - `experiment_tightening`
  - `created_at`

`idea_brief` can be derived from `proposal_outline` for compatibility. `deepening.improved_brief` can become the preferred brief when present.

## Backend Design

Add deterministic normalization helpers:

- `_normalize_idea_brief(candidate, outline, evidence_map)` builds a brief from model output, `proposal_outline`, and legacy candidate fields.
- `_evidence_facets_for_candidate(candidate, evidence_map)` extracts concise evidence facets: problem/task, mechanism signal, evaluation/dataset, limitation, transferable insight.
- `_normalize_deepening_result(raw, idea, project, evidence_map, focus)` normalizes model output and falls back to deterministic improvements when model output is missing.

Generation updates:

- Candidate generation prompt asks for `idea_brief` in addition to `proposal_outline`.
- Persist selected proposals with `review_json.idea_brief`.
- Keep legacy fields unchanged.

Deepening endpoint:

- Add `POST /api/research/ideas/{idea_id}/deepen`.
- Request body includes optional `focus`.
- The service loads the idea, project, review metadata, and evidence context from the generation run.
- The model prompt performs:
  - novelty attack
  - boundary clarification
  - mechanism tightening
  - minimum experiment reduction
  - brief rewrite
- The endpoint updates `review_json.deepening` and `review_json.idea_brief` to the improved brief, then returns the standard idea response.

Fallback:

- If no LLM response is available, produce a deterministic deepening result using existing proposal fields and explicit risk notes.

## Frontend Design

Proposal expanded view:

- Show `Idea Brief` first.
- Prefer `review.deepening.improved_brief`, then `review.idea_brief`, then `review.proposal_outline`, then legacy fields.
- Render brief fields as compact sections:
  - 研究问题
  - 关键洞察
  - 核心假设
  - 方法机制
  - 最小实验
  - 失败条件
  - 下一步行动
- Add a "深入打磨" action near the brief with a small focus input or default focus.
- Collapse secondary content by default:
  - 六维评审
  - 新颖性/相似工作
  - 证据与相似工作
  - 实验质量/执行包
  - 历史版本

The goal is a quieter page: users see the idea first, then open details only when needed.

## Testing

- Backend unit tests should cover:
  - candidate normalization creates `idea_brief`
  - selected proposal persistence stores `idea_brief`
  - deepening updates `review_json.deepening` and preferred `idea_brief`
  - deterministic fallback works without model output
- Frontend contract tests should cover:
  - `IdeaBrief` type exists
  - proposal detail prefers deepened/brief display
  - secondary panels use disclosure controls
  - deepen API wiring exists
