## ADDED Requirements

### Requirement: PDF text selection remains readable
The paper reader SHALL style PDF text selection so selected passages remain readable and adjacent lines do not visually merge into one heavy block.

#### Scenario: User selects multiple PDF lines
- **WHEN** the user highlights text across multiple lines in the PDF reader
- **THEN** the selection uses a lighter translucent overlay
- **AND** line boxes retain enough visual separation to distinguish adjacent selected lines

#### Scenario: Selected text is captured for paper chat
- **WHEN** the user selects PDF text for a quote card
- **THEN** the visual selection styling does not prevent the selected text from being captured for the paper question composer
