## ADDED Requirements

### Requirement: Research Scout honors requested paper counts
The backend SHALL parse explicit requested paper counts from Research Scout prompts, SHALL use depth-based defaults only when the prompt has no count, and SHALL cap final returned candidates at a documented bounded maximum.

#### Scenario: User asks for ten papers
- **WHEN** a Research Scout prompt asks for `10 篇` or `10 papers`
- **THEN** the retrieval target is 10 candidates instead of the standard-depth default.

#### Scenario: User asks for a large survey
- **WHEN** a Research Scout prompt asks to survey 50 papers
- **THEN** the backend targets up to the configured maximum returned candidates
- **AND** metadata records the requested count, final limit, and whether the request was capped.

### Requirement: Research Scout exposes retrieval diagnostics
Research Scout stream metadata SHALL include retrieval diagnostics that distinguish planned queries, internal pool size, final ranked count, requested count, and provider stage counts.

#### Scenario: Candidate pool is larger than final results
- **WHEN** Research Scout retrieves papers from scholarly providers
- **THEN** the metadata reports the candidate pool target and ranked candidate count separately.

#### Scenario: Request cannot be fully satisfied
- **WHEN** scholarly discovery returns fewer ranked papers than the final target
- **THEN** metadata reports the under-filled count
- **AND** the assistant answer explains that the result set is incomplete rather than inventing extra papers.

### Requirement: Research Scout uses broader topic aliases
Research Scout query planning SHALL combine LLM-planned search terms with deterministic task aliases for known research topics so short prompts still retrieve enough candidates.

#### Scenario: Video grounding search
- **WHEN** a user asks for video grounding papers
- **THEN** planned queries include related terms such as temporal grounding, natural language video localization, moment localization, and text-to-video moment retrieval.
