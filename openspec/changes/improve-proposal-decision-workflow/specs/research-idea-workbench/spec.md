## ADDED Requirements

### Requirement: Top Proposal list is rankable
The research project page SHALL allow users to sort persisted Top Proposals using existing review and proposal metadata.

#### Scenario: Sort by review score
- **WHEN** a project has multiple Top Proposals with review metadata
- **THEN** the Top Proposal tab can order them by aggregate review score
- **AND** proposals without aggregate score use available novelty and feasibility score fallbacks

#### Scenario: Sort by recency
- **WHEN** a user chooses recency sorting
- **THEN** the Top Proposal tab orders proposals by creation time without changing the persisted proposal records

### Requirement: Top Proposal list is filterable by decision state
The research project page SHALL allow users to filter Top Proposals by decision status while preserving proposal detail actions.

#### Scenario: Filter pinned proposals
- **WHEN** a user filters the Top Proposal tab to pinned proposals
- **THEN** only pinned proposals are shown
- **AND** existing comparison, validation, discussion, experiment, and writing actions remain available for visible proposals

#### Scenario: Filter has no matches
- **WHEN** the selected decision filter has no matching proposals
- **THEN** the page shows an empty state that explains no proposals match the current filter

### Requirement: Top Proposal decision summary is visible
The research project page SHALL show a concise decision summary and highlight the strongest visible proposal.

#### Scenario: Recommended proposal is highlighted
- **WHEN** the Top Proposal tab contains non-rejected proposals
- **THEN** the highest ranked visible non-rejected proposal is marked as recommended
- **AND** the proposal header exposes its key score signals

#### Scenario: Decision counts are visible
- **WHEN** a user opens the Top Proposal tab
- **THEN** the page shows counts for pending, pinned, rejected, and implemented proposals
