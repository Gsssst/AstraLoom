## ADDED Requirements

### Requirement: Paper chat share cards are collapsed by default
The paper push center SHALL render paper chat share cards in a compact collapsed state by default.

#### Scenario: User opens paper push center
- **WHEN** paper chat share notifications are listed
- **THEN** each share card shows compact metadata and a short preview
- **AND** full shared message bodies are hidden until the user expands the card

#### Scenario: User expands a share card
- **WHEN** the user clicks the expand action on a share card
- **THEN** that card displays the full selected messages with Markdown/LaTeX rendering

#### Scenario: User collapses an expanded card
- **WHEN** the user clicks the collapse action on an expanded share card
- **THEN** the card returns to compact preview mode
