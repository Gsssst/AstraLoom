## MODIFIED Requirements

### Requirement: Scholarly discovery supports planned query variants
The paper discovery workflow SHALL support multiple bounded query variants for one user request.

#### Scenario: Planned variants return overlapping papers
- **WHEN** multiple planned scholarly queries return overlapping papers
- **THEN** the workflow deduplicates candidates by arXiv id, DOI, remote id, or normalized title
- **AND** ranks the merged set before exposing import actions.
