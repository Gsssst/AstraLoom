## ADDED Requirements

### Requirement: Chat exposes Research Scout mode
The chat interface SHALL allow users to switch the current turn into a Research Scout mode focused on discovering useful scholarly papers.

#### Scenario: User selects Research Scout
- **WHEN** the user selects Research Scout mode in chat
- **THEN** subsequent chat requests include `assistant_mode=research_scout`
- **AND** the interface explains that this mode searches for interesting and useful papers.

#### Scenario: User returns to general chat
- **WHEN** the user switches back to general mode
- **THEN** subsequent chat requests include `assistant_mode=general`
- **AND** the normal chat behavior remains available.

### Requirement: Research Scout produces structured candidates
The backend SHALL return structured paper candidates when Research Scout mode is used and scholarly discovery returns results.

#### Scenario: Scholarly search returns papers
- **WHEN** a Research Scout request searches for a topic and supported scholarly providers return results
- **THEN** the stream metadata includes candidate papers with title, authors, year, source, URL, optional PDF URL, abstract, and recommendation rationale.

#### Scenario: Scholarly search returns no papers
- **WHEN** a Research Scout request returns no scholarly candidates
- **THEN** the assistant explains that no candidates were found and suggests query refinements.

### Requirement: Research Scout explains usefulness
The assistant SHALL explain why recommended papers are interesting and useful for the user's research instead of only listing titles.

#### Scenario: Candidate recommendation is generated
- **WHEN** Research Scout returns candidate papers
- **THEN** the assistant answer includes a ranked reading suggestion with usefulness rationale and at least one caveat or follow-up search direction.

### Requirement: Research Scout status is visible
The chat stream SHALL show discovery-specific status messages while Research Scout mode is running.

#### Scenario: Research Scout stream begins
- **WHEN** a Research Scout request starts
- **THEN** the stream status indicates that scholarly sources are being searched.

#### Scenario: Research Scout metadata is received
- **WHEN** structured candidates are available
- **THEN** the frontend displays them as paper discovery cards near the assistant answer.

### Requirement: Research Scout candidates are actionable
The chat interface SHALL allow a user to turn a Research Scout candidate into a saved paper library item without leaving the chat workflow.

#### Scenario: User ingests a candidate
- **WHEN** a candidate card has a supported scholarly source and remote identifier
- **AND** the user clicks "加入论文库"
- **THEN** the frontend calls the personal ingest endpoint with the candidate source, remote identifier, and server-issued ingest token
- **AND** the card shows a saved state after success.

#### Scenario: User refines the scout search
- **WHEN** Research Scout returns candidates
- **THEN** the interface offers follow-up search intents such as baseline, survey, latest, and counterexample
- **AND** selecting one prepares a Research Scout prompt with automatic deep scholarly search enabled.

### Requirement: Chat uses a workbench-style reading layout
The chat interface SHALL present long assistant answers in a centered, readable workbench stream rather than a full-width decorative bubble feed.

#### Scenario: User reads a normal or Research Scout answer
- **WHEN** chat messages render
- **THEN** assistant content is constrained to a comfortable reading width
- **AND** references and Research Scout cards remain visually attached to the answer.
