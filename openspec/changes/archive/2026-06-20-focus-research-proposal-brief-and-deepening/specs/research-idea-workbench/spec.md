## ADDED Requirements

### Requirement: Selected proposals prioritize a compact idea brief
The research idea workbench SHALL expose a compact idea brief for selected proposals so users can quickly understand the proposed research direction before inspecting detailed review metadata.

#### Scenario: Persist selected proposal idea brief
- **WHEN** a candidate is persisted as a selected proposal
- **THEN** its review metadata includes an `idea_brief`
- **AND** the brief includes research question, key insight, core hypothesis, mechanism, minimum experiment, failure condition, and next actions
- **AND** legacy fields such as description, hypothesis, approach, experiment plan, review scores, and proposal outline remain available

#### Scenario: Normalize missing idea brief
- **WHEN** model output omits part or all of the compact brief
- **THEN** the backend derives missing brief fields from proposal outline, gap, hypothesis, approach, risks, minimum experiment, and evidence metadata

#### Scenario: Open proposal detail
- **WHEN** a user expands a proposal
- **THEN** the interface displays the compact idea brief before review scores, evidence details, novelty matrices, and execution metadata
- **AND** secondary review and evidence details are collapsed by default while remaining inspectable

### Requirement: Focused deepening for one selected proposal
The research idea workbench SHALL allow a project owner to deepen one selected proposal without starting a new full generation run.

#### Scenario: Deepen proposal with optional focus
- **WHEN** the user requests deepening for a selected proposal with an optional focus note
- **THEN** the backend critiques novelty, clarifies scope boundaries, tightens the mechanism, reduces the minimum experiment, and rewrites the compact brief
- **AND** the result is stored in proposal review metadata
- **AND** the updated idea response exposes the improved brief

#### Scenario: Deepening uses proposal evidence facets
- **WHEN** deepening runs for a proposal with available evidence metadata
- **THEN** the prompt receives concise evidence facets for problem/task, mechanism signal, evaluation/dataset, limitation, and transferable insight
- **AND** the stored deepening result records which facets were used

#### Scenario: Deepening fallback
- **WHEN** model output is unavailable or invalid during deepening
- **THEN** the backend stores a deterministic deepening result using the existing proposal fields and explicit limitations instead of failing the request
