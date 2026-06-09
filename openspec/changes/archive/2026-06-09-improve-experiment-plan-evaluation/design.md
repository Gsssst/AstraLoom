## Context

The current workbench already stores a `minimum_experiment` and computes `experiment_completeness`, but the score is mostly a checklist. It rewards having any dataset, baseline, metrics, and steps, while underweighting whether the plan can actually support a paper-grade claim.

Related project patterns reviewed before implementation:

- AI-Researcher: ranks and filters generated research proposals after related-paper grounding.
- AI-Scientist: treats idea generation, experiment execution, and review as separate quality gates.
- CodeScientist-style workflows: expose experiment plans before execution so users can edit weak setup details.
- AblationBench-style evaluation work: highlights that ablation planning is a distinct quality dimension, not just an optional step.

## Goals

- Improve proposal ranking by preferring plans with testable, reproducible, and claim-aligned experiments.
- Surface exactly why an experiment plan is weak before the user starts coding or writing.
- Preserve compatibility with the existing `minimum_experiment` shape.

## Non-Goals

- Do not add experiment execution automation in this change.
- Do not require a new table or migration.
- Do not call an LLM or external API for experiment scoring.
- Do not add another planning page.

## Approach

### Experiment Quality Profile

Extend the existing deterministic experiment profile with a richer nested `quality_profile`:

- `dataset_score`: dataset is named, concrete, and not only a generic placeholder.
- `baseline_score`: includes a strong baseline, simple baseline, and ideally the closest prior/nearest collision when available.
- `metric_score`: includes task-quality metrics and, when relevant, efficiency/robustness/statistical metrics.
- `ablation_score`: includes component ablation, no-change/no-enhancement control, and sensitivity/failure-slice checks.
- `statistical_score`: includes repeated runs, significance/confidence intervals, variance, or stability criteria.
- `feasibility_score`: checks compute/resource wording against generation constraints and penalizes unrealistic large-model plans under low-compute budgets.
- `falsification_score`: rewards explicit failure criteria and measurable rejection conditions.

The top-level `experiment_completeness` remains available for compatibility but gains:

- `quality_score`
- `readiness`
- `blocking_issues`
- `recommended_fixes`
- `quality_profile`

### Ranking Adjustment

`apply_quality_adjustments` will use `quality_score` instead of only the old completeness value for feasibility and testability deltas. Ranking should penalize:

- missing dataset or baselines
- no strong baseline
- no ablation or control
- no statistical validity signal
- compute mismatch with low-compute/reproducible constraints

### Persistence and UI

Persist the enriched profile through existing `review_json.experiment_completeness`. The proposal detail view will display a compact experiment quality summary with readiness, quality score, blocking issues, and recommended fixes.

## Risks

- Deterministic keyword scoring can misread domain-specific plans. Mitigation: treat it as a ranking aid and keep the explanatory profile visible.
- Existing tests may assume old completeness thresholds. Mitigation: preserve old fields and adjust only where richer quality improves correctness.
