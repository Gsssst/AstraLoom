## ADDED Requirements

### Requirement: Paper chat typing does not re-render the whole paper detail page
Paper detail chat composer input SHALL keep draft text in local composer state and only synchronize with parent state when submitting, clearing, or restoring a failed question.

#### Scenario: User types in the paper chat composer
- **GIVEN** the paper detail page has loaded a PDF and prior chat messages
- **WHEN** the user types text in the chat composer
- **THEN** the draft text updates locally in the composer
- **AND** the parent paper detail page does not need to update its top-level question state on every keystroke

#### Scenario: Failed submission restores draft text
- **GIVEN** a non-template paper chat submission fails
- **WHEN** the failure is handled
- **THEN** the composer draft is restored to the visible question text
