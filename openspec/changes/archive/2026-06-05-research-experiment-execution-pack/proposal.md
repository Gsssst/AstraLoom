# Change: Research Experiment Execution Pack

## Motivation

Research Ideas already contain minimum experiments, validation signals, and feedback evolution, but users still need to mentally stitch together what to run first, what evidence is missing, and how recorded results should drive the next iteration. This makes the "idea to experiment" loop feel scattered.

## What Changes

- Add a deterministic experiment execution pack for each Research Idea.
- Summarize readiness, minimum experiment tasks, success metrics, feedback status, missing items, and next actions.
- Expose the pack through a dedicated API endpoint.
- Surface the pack in the Research Project proposal panel so users can progress an Idea without hunting across tabs.

## Non-Goals

- Do not replace the existing Idea generation algorithm.
- Do not generate runnable experiment code in this change.
- Do not introduce a new experiment database model.

## References

- AutoResearch-style loops emphasize stage continuity from idea to experiment feedback.
- AI-Scientist-like workflows keep experiment plans falsifiable and tied to measurable outcomes.
