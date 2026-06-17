## ADDED Requirements

### Requirement: Paper Q&A retrieves bibliography entries for reference-list questions
The paper Q&A evidence retriever SHALL detect user questions about a paper's reference list or a numbered bibliography entry and SHALL prioritize evidence from the References/Bibliography section over ordinary in-text citation contexts.

#### Scenario: User asks for Reference [1]
- **WHEN** a user asks what `Reference [1]` or the first referenced paper is
- **AND** the paper text contains a numbered References/Bibliography section
- **THEN** the retrieved evidence includes the bibliography entry numbered `1`
- **AND** body text that merely cites another reference number does not replace the bibliography entry.

#### Scenario: Reference list cannot be located
- **WHEN** a user asks for a specific reference number
- **AND** the retriever cannot locate a References/Bibliography section
- **THEN** the evidence plan records a reference-list warning
- **AND** the answer context instructs the model to say the bibliography list was not found instead of guessing.

#### Scenario: User asks broadly about references
- **WHEN** a user asks to inspect or summarize the paper's references without a specific number
- **THEN** the retrieved evidence includes a compact catalog from the detected References/Bibliography section.
