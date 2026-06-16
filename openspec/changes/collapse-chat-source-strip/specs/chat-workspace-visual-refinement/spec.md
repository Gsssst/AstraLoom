## MODIFIED Requirements

### Requirement: Chat source strips stay compact by default
Chat message source/reference strips SHALL render in a collapsed one-line summary by default when references are available.

#### Scenario: Research Scout message has many paper sources
- **WHEN** an assistant Research Scout message has multiple paper candidate references
- **THEN** the message shows a compact `论文候选来源` summary with the visible reference count
- **AND** it does not render every source tag until the user expands the strip

#### Scenario: User expands source strip
- **WHEN** the user clicks the source strip expand control
- **THEN** the full reference tag list is shown with the existing tooltip and source-opening behavior

#### Scenario: Generic chat message has references
- **WHEN** a non-Research Scout assistant message has retrieval references
- **THEN** the collapsed source summary uses `检索来源`
- **AND** expanding the strip reveals the same references previously shown inline
