## ADDED Requirements

### Requirement: Adaptive Paper Evidence Strategy
Paper Q&A SHALL select an evidence strategy based on question intent instead of using one fixed evidence budget for all questions.

#### Scenario: Ordinary factual question remains compact
- **WHEN** a user asks a narrow factual question about a current paper
- **THEN** the system SHALL use a compact evidence strategy with the default evidence budget
- **AND** the response references SHALL remain page-aware when page data is available.

#### Scenario: Local table question uses table packs
- **WHEN** a user asks for a specific table value, metric, baseline, or ablation
- **THEN** the system SHALL prioritize table evidence packs over isolated text chunks
- **AND** selected table bodies SHALL be included completely.

#### Scenario: Broad experiment question uses experiment dossier
- **WHEN** a user asks to analyze the whole experiment, evaluation, results, all tables, benchmarks, baselines, metrics, or ablations
- **THEN** the system SHALL build an experiment evidence dossier
- **AND** the retrieval scope SHALL disclose that experiment dossier mode was used.

### Requirement: Experiment Evidence Dossier
For broad experiment questions, Paper Q&A SHALL provide a global experiment evidence package before asking the model to answer.

#### Scenario: Dossier includes table catalog
- **WHEN** structured table blocks are available
- **THEN** the experiment dossier SHALL include a catalog entry for every available table
- **AND** each catalog entry SHALL include page, parser source, table index when available, inferred caption when available, columns, row count, and table quality metadata when available.

#### Scenario: Dossier includes full selected tables
- **WHEN** experiment-related tables are available
- **THEN** the evidence bundle SHALL include complete table packs for the selected experiment-related tables
- **AND** selected table bodies SHALL NOT be character-truncated.

#### Scenario: Dossier includes experiment text
- **WHEN** experiment, evaluation, result, conclusion, or limitation text snippets are available
- **THEN** the evidence bundle SHALL include multiple relevant text snippets around those sections
- **AND** table catalog evidence SHALL remain distinguishable from text evidence in references.

#### Scenario: Many tables remain bounded
- **WHEN** a paper contains more tables than can fit as full table packs
- **THEN** the dossier SHALL still list all tables in the catalog
- **AND** the system SHALL cap full table packs by count rather than truncating selected table bodies.
