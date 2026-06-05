## Overview

This change upgrades the existing evidence-grounded workbench without replacing it. The current stages already match a good research-agent foundation: evidence collection, Gap Map, candidate generation, deduplication, six-dimensional review, and persistence. v3 adds three inspectable quality gates between generation and selection.

## References And Borrowed Patterns

- `SakanaAI/AI-Scientist`: Borrow the idea that research generation should include novelty checks, experiment plans, and AI review instead of one-shot brainstorming.
- `AI-Scientist-v2`: Borrow the progressive tree-search framing, but keep our MVP lightweight and deterministic enough to test.
- `cheerss/SciPIP`: Borrow paper-grounded idea proposal: ideas should be derived from literature gaps and evidence, not freeform imagination.
- `future-house/paper-qa`: Borrow the principle that scientific claims should remain tied to cited evidence.
- `stanford-oval/storm`: Borrow structured research/writing flow: collect perspectives first, then outline/generate.

## Backend Design

### Candidate Search Tree

After `generate_candidates`, call `expand_candidate_tree`. The method:

- Accepts initial candidates.
- Keeps a small beam of high-potential candidates.
- Generates deterministic variants with operators:
  - `strong_baseline`: strengthen baseline and metrics.
  - `failure_mode`: focus on failure cases and falsification.
  - `cost_aware`: add efficiency or resource constraints.
- Annotates each candidate with:
  - `tree.round`
  - `tree.parent_title`
  - `tree.operator`
  - `tree.lineage`

### Novelty Check

`novelty_check_candidates` compares candidate title/hypothesis/approach against evidence title/abstract tokens. It returns:

- `status`: `likely_novel`, `incremental`, or `too_similar`
- `score`: 0-1
- `nearest_evidence`
- `rationale`

This check is intentionally conservative: high similarity lowers novelty.

### Adversarial Review

`adversarial_review_candidates` checks each candidate for common failure modes:

- missing strong baseline
- weak falsification test
- weak evidence coverage
- vague or missing metrics
- experiment cost risk

It returns objections, required fixes, verdict, and penalty. The final candidate score is adjusted by novelty status and adversarial penalty.

### Persistence

`persist_top_proposals` stores:

- `review_json.novelty_check`
- `review_json.adversarial_review`
- `review_json.search_tree`
- adjusted aggregate score

## Frontend Design

Research Proposal cards display:

- 新颖性状态 and score.
- 最近相似证据 if any.
- 反驳评审 verdict and top objections.
- 搜索树来源: round/operator/parent.

## Risks

- Deterministic novelty check is lexical, not a substitute for full scholarly novelty. The UI must present it as a signal, not a final truth.
- More candidates can increase runtime if LLM expansion is used. MVP uses deterministic variants to keep performance stable.
