## MODIFIED Requirements

### Requirement: Research Scout candidate cards are visible for paper discovery
Research Scout SHALL surface structured candidate cards and evaluation metadata for paper discovery responses.

#### Scenario: Scholarly discovery returns candidates
- **WHEN** Research Scout finds candidate papers
- **THEN** the assistant message metadata includes candidate cards
- **AND** each card includes import/classification/project actions
- **AND** each card includes evaluation dimensions or a heuristic fallback
- **AND** venue/year constraints are represented in intent and constraint match metadata.

#### Scenario: Scholarly discovery returns no candidates
- **WHEN** Research Scout finds no candidate papers
- **THEN** the response explains that scholarly discovery returned no candidates
- **AND** it does not fall back to unrelated generic web pages as if they were paper evidence.
