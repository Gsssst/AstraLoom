## ADDED Requirements

### Requirement: Related-paper recommendations are cached per research project
The system SHALL cache related-paper recommendation results for a research project and SHALL reuse the cache when the project recommendation inputs have not changed.

#### Scenario: Open a project with cached recommendations
- **WHEN** a user opens a research project whose name, description, keywords, and attached paper IDs match the cached recommendation key
- **THEN** the related-paper recommendation endpoint returns cached recommendations without recomputing the selection pipeline

#### Scenario: Project inputs changed
- **WHEN** a user opens a research project after its recommendation inputs change
- **THEN** the related-paper recommendation endpoint recomputes recommendations and stores a fresh cache entry

### Requirement: Related-paper recommendations can be manually refreshed
The system SHALL provide a way to recompute related-paper recommendations even when a valid cache exists.

#### Scenario: User refreshes related papers
- **WHEN** a user requests a recommendation refresh for a research project
- **THEN** the system recomputes related-paper recommendations, updates the cache, and returns the refreshed result

#### Scenario: Related-papers panel shows cache state
- **WHEN** the research project page displays related papers
- **THEN** the panel indicates whether the data came from cache and provides a refresh control
