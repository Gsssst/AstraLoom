## ADDED Requirements

### Requirement: Research Scout runs a bounded paper-discovery agent
Research Scout SHALL use a bounded backend agent loop that lets the model choose from declared paper-discovery tools, while the backend validates tool arguments, executes tools, records observations, and enforces stop limits.

#### Scenario: Agent chooses a valid tool
- **WHEN** a Research Scout request requires external paper discovery
- **THEN** the backend provides the model with the available Research Scout tool schema
- **AND** executes only a validated tool call from that schema
- **AND** records the validated arguments and observation in the tool trace.

#### Scenario: Agent emits invalid action
- **WHEN** the model returns invalid JSON, an unknown tool name, or invalid tool arguments
- **THEN** the backend rejects that action
- **AND** gives the model bounded error feedback or falls back to deterministic retrieval
- **AND** does not execute arbitrary or unregistered tools.

#### Scenario: Agent reaches budget
- **WHEN** the agent reaches the configured max steps, provider-call budget, or workflow timeout
- **THEN** it stops retrieval
- **AND** returns the best validated candidates found so far or an explicit no-candidate explanation
- **AND** includes the stop reason in trace metadata.

### Requirement: Research Scout preserves hard query constraints
Research Scout SHALL represent requested count, year range, venue, institution, author, dataset, task, method, and preference constraints as structured state and SHALL enforce hard constraints before final candidate cards are returned.

#### Scenario: User asks for a year range
- **WHEN** the user asks for papers from 2025 to 2026
- **THEN** search tools receive `year_from=2025` and `year_to=2026`
- **AND** final candidates outside that range are excluded when the year is known
- **AND** candidates with unknown year are marked as unverified or excluded according to constraint mode.

#### Scenario: User asks for a venue
- **WHEN** the user asks for CVPR papers
- **THEN** the agent state includes `venues=["CVPR"]`
- **AND** final candidates must include matched or official venue evidence when venue is a hard constraint
- **AND** candidates without venue evidence are not presented as satisfying the venue request.

#### Scenario: User asks for an institution
- **WHEN** the user asks for papers from a specific university, lab, or company
- **THEN** the agent state includes normalized institution constraints
- **AND** final cards show institution evidence and provenance when available
- **AND** the assistant states when provider metadata cannot confirm the institution instead of fabricating an affiliation.

### Requirement: Research Scout can recover by changing search strategy
Research Scout SHALL inspect tool observations and decide whether to broaden, narrow, or retry searches before generating the final answer.

#### Scenario: First search returns too few candidates
- **WHEN** the first retrieval tool returns fewer validated candidates than the requested target
- **THEN** the agent can call additional tools with expanded aliases, alternate task names, or broader providers
- **AND** the trace explains why the retry was performed.

#### Scenario: Search results fail constraints
- **WHEN** retrieved candidates are mostly excluded by year, venue, or institution constraints
- **THEN** the agent can retry using constraint-aware provider arguments
- **AND** final output reports how many candidates were excluded by the constraint.

### Requirement: Research Scout returns evidence-grounded candidate cards
Research Scout SHALL prepare candidate cards only from retrieved and validated paper candidates and SHALL attach evaluation, provenance, source, PDF status, and user-confirmed action metadata.

#### Scenario: Candidates are found
- **WHEN** the agent has validated final candidates
- **THEN** each card includes title, authors, year, venue when known, source, source URL, PDF URL when known, import token, constraint matches, evaluation dimensions, and provenance where available
- **AND** the assistant recommendation references only those candidate cards.

#### Scenario: No candidates satisfy constraints
- **WHEN** no retrieved candidates satisfy hard constraints
- **THEN** Research Scout returns no fabricated cards
- **AND** the assistant explains which constraints prevented results
- **AND** suggests follow-up search queries or relaxed constraints.

### Requirement: Research Scout side effects require user confirmation
Research Scout SHALL NOT autonomously import papers, create folders, add papers to projects, or mutate user library state during the discovery loop.

#### Scenario: Agent finds importable papers
- **WHEN** a candidate card has an import token
- **THEN** the card can show import, folder, and project actions
- **AND** those actions execute only after the user explicitly clicks or confirms them.
