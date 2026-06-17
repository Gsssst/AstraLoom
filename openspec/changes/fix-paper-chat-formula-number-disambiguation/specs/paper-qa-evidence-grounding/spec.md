## ADDED Requirements

### Requirement: Numbered formula retrieval uses reading page context
Paper Q&A evidence retrieval SHALL prefer numbered formula evidence from the user's current PDF page when the user asks about an explicit formula number and a current page is available.

#### Scenario: Same formula number appears on multiple pages
- **GIVEN** page text contains a formula labeled `(2)` on page 3 and another formula labeled `(2)` on page 5
- **AND** the paper chat request includes current PDF page 5
- **WHEN** the user asks to explain formula 2
- **THEN** retrieved formula evidence targets the page 5 formula before page 3 evidence

#### Scenario: Current page has no requested formula number
- **GIVEN** the paper chat request includes current PDF page 5
- **AND** page 5 does not contain formula `(2)`
- **AND** another page contains formula `(2)`
- **WHEN** the user asks to explain formula 2
- **THEN** retrieval falls back to the available formula `(2)` evidence

#### Scenario: Explicit PDF quote remains authoritative
- **GIVEN** the user asks with selected PDF quote text from page 5
- **AND** current PDF page context is also present
- **WHEN** retrieving evidence
- **THEN** the selected quote/page remains represented in the user question and page preference is consistent with the quoted page
