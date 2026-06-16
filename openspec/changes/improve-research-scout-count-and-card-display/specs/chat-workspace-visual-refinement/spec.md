## ADDED Requirements

### Requirement: Research Scout cards handle long metadata labels
The chat workspace SHALL constrain long Research Scout metadata labels so venue, provenance, constraint, and source tags cannot overflow their candidate card.

#### Scenario: Long venue title
- **WHEN** a candidate has a long conference or journal title
- **THEN** the tag is visually bounded inside the card
- **AND** the full label remains available through tooltip or hover affordance.

### Requirement: Research Scout displays returned candidates progressively
The chat workspace SHALL not hard-cap Research Scout candidate cards to six when the backend returns more candidates, and SHALL provide a compact way to expand or collapse longer candidate lists.

#### Scenario: More than ten candidates
- **WHEN** Research Scout returns more than ten candidates
- **THEN** the chat initially shows a bounded readable subset
- **AND** the user can expand the card list to view the remaining returned candidates.

#### Scenario: Ten or fewer candidates
- **WHEN** Research Scout returns ten or fewer candidates
- **THEN** all returned candidate cards are visible without requiring expansion.
