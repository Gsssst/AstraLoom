## Overview

The validation loop will reuse data already produced by the research idea pipeline instead of calling the LLM again. The goal is to turn existing artifacts into a compact decision aid:

- `evidence_json.items`: paper snippets and retrieved evidence already associated with an idea.
- `review_json.novelty_check`: nearest evidence and novelty/collision status.
- `review_json.adversarial_review`: objections, missing baselines, and metric concerns.
- `experiment_plan`: datasets, baselines, metrics, steps, and expected outcome.

## Backend

Add a deterministic `validate_idea` method to `ResearchIdeaWorkbench`. It will return:

- `collision_risk`: level, status, score, reason, and nearest related work.
- `related_work`: top evidence items and nearest evidence from novelty check.
- `feasibility_risks`: normalized risks derived from adversarial objections, low scores, and missing plan fields.
- `experiment_checklist`: grouped minimum checklist for datasets, baselines, metrics, ablations, implementation steps, and reproducibility.
- `writing_readiness`: status, label, reasons, and suggested next actions.
- `coverage`: lightweight counts for evidence, referenced papers, and experiment completeness.

The validation method should not mutate the idea by default. This keeps it cheap, repeatable, and safe to call from UI cards.

## API

Add `GET /api/research/ideas/{idea_id}/validation`.

The route will:

- Use the existing owned-idea authorization helper.
- Load the owning research project for context.
- Return the structured validation payload.

## Frontend

Extend `ResearchProjectPage.tsx`:

- Add per-idea validation state and loading state.
- Add a "验证闭环" action in each idea card.
- Render a compact validation panel with:
  - writing readiness badge;
  - collision/novelty status;
  - related/conflicting evidence;
  - risks;
  - experiment checklist;
  - next actions.

The UI should default to concise summaries and only show the panel after the user requests validation, so existing cards do not become noisy.

## Testing

- Unit-test `validate_idea` for high collision/incomplete experiment and ready/completed experiment cases.
- Add route coverage to multi-user authorization tests.
- Add a frontend source contract test that confirms the page calls the validation endpoint and exposes the validation panel labels.
