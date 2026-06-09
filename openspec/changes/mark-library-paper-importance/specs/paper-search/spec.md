## MODIFIED Requirements

### Requirement: Local paper search returns actionable paper cards
Local paper search SHALL return enough metadata for the frontend to render actionable paper cards, including source links, import ownership, processing state, reading state when available, and shared importance marker metadata.

#### Scenario: Marked paper appears in search results
- **WHEN** a local library paper has a shared importance marker
- **AND** the user searches or browses the paper library
- **THEN** the paper card response includes the marker label and note
