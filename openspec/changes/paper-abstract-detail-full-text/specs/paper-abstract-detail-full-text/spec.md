## ADDED Requirements

### Requirement: Complete abstract in card detail view
The paper-library interface SHALL display the complete available scholarly abstract in the card detail modal while retaining a concise card preview.

#### Scenario: Abstract is longer than preview limit
- **WHEN** a search result has an abstract longer than 500 characters and the user opens “查看摘要”
- **THEN** the card remains concise and the modal displays the complete available abstract

#### Scenario: Compatibility fallback
- **WHEN** a result does not contain a dedicated complete-abstract field
- **THEN** the modal displays the available preview abstract instead

