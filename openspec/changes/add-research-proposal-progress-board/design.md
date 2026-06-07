## Context

The Research Project page currently lists Top Proposals and lets users individually run validation, inspect execution packs, discuss with Copilot, record experiments, and inspect timelines. Those capabilities are useful but require manual triage. The backend already has deterministic validation and execution-pack services, so a board can derive status and priority without additional storage or model calls.

## Goals / Non-Goals

**Goals:**
- Provide a project-level read-only progress board for accessible Proposals.
- Classify Proposals by actionable next state and include priority, blockers, signals, and recommended action.
- Expose a frontend board tab that supports scanning and direct next-step actions.
- Reuse existing validation, execution pack, experiment, timeline, writing, and evolution flows.

**Non-Goals:**
- Add a new persisted workflow state machine.
- Replace manual Proposal status values (`draft`, `pinned`, `rejected`, `implemented`).
- Auto-run experiments or model calls.
- Add drag-and-drop board editing.

## Decisions

- **Derive board state on demand.** This avoids a migration and keeps board results consistent with validation and experiment feedback.
- **Keep board statuses stable.** The API returns fixed status keys so the UI can group columns deterministically.
- **Explain priority rather than hide it.** Each card includes score factors and blockers so users can understand why it is ranked.
- **Map recommended actions to existing UI functions.** The frontend should call existing validation, execution pack, Copilot, experiment, writing, and timeline handlers instead of duplicating logic.

## Risks / Trade-offs

- Derived priority may feel opinionated -> expose contributing signals and keep manual status actions available.
- Board computation can be heavier for many Proposals -> keep per-Proposal validation deterministic and avoid model calls.
- Some next actions cannot be fully automatic -> use the action to open the relevant existing panel or workflow.
