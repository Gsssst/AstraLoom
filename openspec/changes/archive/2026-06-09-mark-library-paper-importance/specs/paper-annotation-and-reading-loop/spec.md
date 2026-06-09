## MODIFIED Requirements

### Requirement: Paper detail supports personal and shared reading context
Paper detail SHALL show personal reading state, personal save state, annotations, and shared paper-level signals that help the team prioritize reading.

#### Scenario: Paper is marked important or interesting
- **WHEN** a user opens a marked paper detail page
- **THEN** the page displays the shared marker prominently near the paper metadata

#### Scenario: Signed-in user changes the shared marker
- **WHEN** a signed-in user sets or clears the shared marker from paper detail
- **THEN** the page updates immediately after the API confirms the change
