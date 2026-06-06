## Context

The backend `workbench-summary` endpoint already returns enough structured state for project stage, risk level, progress, evidence, citations, submission template status, warnings, quick links, and next actions. The current frontend renders those fields, but the overview is visually similar to the rest of the page and next actions are placed below metric cards.

Comparable open-source writing tools commonly emphasize workflow orientation: OpenPrism-style workspaces keep the active document and diagnostic context close together; Fidus Writer foregrounds structured academic content and citations; OpenDraft-style assistants treat generation, verification, and export as staged steps. This change applies that pattern without changing the project's backend contract.

## Goals / Non-Goals

**Goals:**
- Make the selected writing project's stage and risk immediately visible.
- Convert next actions and blockers into compact, clickable workflow controls.
- Preserve existing project editing and export behaviors.
- Keep the implementation frontend-only and deterministic from existing summary fields.

**Non-Goals:**
- Add a new writing summary endpoint or change the response schema.
- Redesign the full writing page navigation.
- Change generation, citation, quality-check, evidence-table, or export logic.
- Add official venue template parsing behavior beyond the existing panel.

## Decisions

- Build a frontend-only stage strip from `workbenchSummary`.
  - Rationale: the backend already computes project state; the UI needs better presentation rather than new data.
  - Alternative considered: adding backend-specific blocker fields; deferred because the UI can derive the current blocker chips from existing summary/progress/evidence/citation/submission fields.
- Put next actions above metric cards.
  - Rationale: users visit the workbench to decide what to do next; metrics support that decision but should not bury the action.
  - Alternative considered: keep next actions in a list after warnings; rejected because the page currently reads too much like a report.
- Use compact chips/buttons instead of adding another nested card layer.
  - Rationale: the project page already contains cards for creation, export, sections, and evidence. A dense strip keeps the workbench scannable.

## Risks / Trade-offs

- [Risk] Derived blocker labels can drift from backend summary wording.
  -> Mitigation: derive only from stable existing fields and keep labels descriptive rather than duplicating backend warning strings.
- [Risk] More controls can crowd smaller screens.
  -> Mitigation: use wrapping `Space`, responsive columns, and short labels.
- [Risk] Users may treat the readiness strip as a hard gate.
  -> Mitigation: preserve wording as suggested next actions and keep all existing tools available.
