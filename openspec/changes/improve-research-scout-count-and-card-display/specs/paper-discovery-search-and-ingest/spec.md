## ADDED Requirements

### Requirement: Scholarly discovery separates pool size from final count
The system SHALL retrieve a larger bounded candidate pool than the final requested result count when Research Scout needs ranked paper recommendations.

#### Scenario: Research Scout ranks ten papers
- **WHEN** Research Scout targets 10 final papers
- **THEN** scholarly discovery gathers more than 10 internal candidates before de-duplication and ranking.

#### Scenario: Research Scout ranks many papers
- **WHEN** Research Scout targets a large final count
- **THEN** provider calls remain bounded by configured per-query and total-pool limits
- **AND** the final ranked response is capped to the final count.

### Requirement: Scholarly discovery expands known task aliases
The system SHALL expand known research topic names into common scholarly aliases before querying remote providers.

#### Scenario: Video grounding aliases
- **WHEN** the query is about video grounding
- **THEN** provider searches include aliases for temporal sentence grounding, natural language video localization, video moment retrieval, and moment localization.
