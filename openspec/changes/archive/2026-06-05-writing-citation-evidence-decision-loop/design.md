## Context

The backend already classifies citation roles and computes sentence-paper match status. The writing page already displays some tags, but the result is still a list of papers rather than a decision surface that helps the user write a grounded sentence.

## Goals / Non-Goals

**Goals:**
- Derive a deterministic `decision_label`, `decision_action`, and `decision_warning` for each citation recommendation.
- Show the user how each citation should be used: supporting evidence, baseline, counterexample/limitation, or background.
- Make weak matches explicit and actionable.
- Keep existing endpoints and payload fields compatible.

**Non-Goals:**
- Add a new LLM citation verifier in this iteration.
- Change the retrieval algorithm.
- Store citation decisions in the database.
- Replace project-level evidence cards.

## Decisions

- Compute decision metadata from existing role and match status.
  - Rationale: it is deterministic, fast, and avoids another LLM call.
  - Alternative considered: ask the LLM to judge every recommendation. That may produce richer explanations, but it is slower and less reproducible.
- Keep the main recommendation endpoint unchanged and only add fields.
  - Rationale: no frontend or API compatibility break.
- Improve UI with grouped decision cards rather than adding another tab.
  - Rationale: users are already in the citation recommendation flow; making the existing surface better is less disruptive.

## Risks / Trade-offs

- [Risk] Heuristic decisions can overstate support. → Mitigation: weak and partial matches explicitly ask the user to verify or supplement evidence.
- [Risk] UI becomes noisy. → Mitigation: show concise tags first, explanations second.
- [Risk] Users may treat role labels as final truth. → Mitigation: phrase labels as recommended usage, not proof.
