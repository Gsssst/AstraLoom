# Design: Research Experiment Execution Pack

## Overview

The execution pack is a deterministic service summary built from:

- `ResearchIdea.experiment_plan`
- `ResearchIdea.review_json`
- `ResearchIdea.evidence_json`
- existing experiment records linked to the Idea
- existing validation output

It gives the frontend a single object that can be rendered as an execution panel.

## Pack Shape

```json
{
  "idea_id": "...",
  "readiness": {"status": "ready|needs_setup|needs_feedback", "label": "...", "score": 0.78},
  "summary": "...",
  "minimum_tasks": [{"key": "dataset", "label": "...", "status": "ready|missing", "detail": "..."}],
  "success_metrics": [{"name": "mIoU", "target": "beat strong baseline or explain failure"}],
  "feedback": {"count": 1, "latest": {...}, "has_results": true},
  "risks": [{"level": "medium", "message": "..."}],
  "next_actions": ["记录第一轮实验反馈", "根据反馈演化 Proposal"]
}
```

## Heuristics

- Dataset, baselines, metrics, and steps are each converted into task items.
- Existing experiments linked to the Idea are counted as feedback.
- If feedback exists and has results, the pack recommends feedback-driven evolution.
- If checklist items are missing, the pack recommends completing the minimum experiment setup first.
- Review objections and validation risks are surfaced as experiment risks.

## UI

The proposal detail panel should show the execution pack before the raw minimum experiment. This keeps the user oriented around action rather than metadata.
