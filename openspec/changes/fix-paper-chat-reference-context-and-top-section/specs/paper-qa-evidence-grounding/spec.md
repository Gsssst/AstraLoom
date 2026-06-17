## ADDED Requirements

### Requirement: Numbered Reference Citation Context
Paper Q&A SHALL include in-body citation context when answering a numbered reference lookup if the current paper text contains citations to that reference number.

#### Scenario: User asks how reference one relates to the paper
- **WHEN** the user asks for reference `[1]` and its relationship to the current paper
- **THEN** retrieved evidence includes the bibliography entry for `[1]`
- **AND** retrieved evidence includes one or more body citation context snippets where `[1]` appears when available.

#### Scenario: Body citation context is unavailable
- **WHEN** the bibliography entry is found but no body citation context for that reference number is detected
- **THEN** the answer context distinguishes that the bibliography entry is known while the in-body citation context was not located.
