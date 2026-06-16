## ADDED Requirements

### Requirement: Targeted section evidence reports section match confidence
Paper Q&A evidence metadata SHALL distinguish exact numbered-section retrieval from generic multi-reference coverage.

#### Scenario: Numbered section is matched
- **WHEN** a user asks about a specific numbered section and retrieval returns the matching section range
- **THEN** the API evidence metadata includes the requested section number, matched heading, and a section match flag
- **AND** the evidence metadata marks coverage as sufficient for the targeted section answer

#### Scenario: Numbered section is not matched
- **WHEN** a user asks about a specific numbered section and retrieval falls back to other evidence
- **THEN** the API evidence metadata does not mark a section match
- **AND** generic evidence count coverage remains in effect
