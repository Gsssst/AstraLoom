## MODIFIED Requirements

### Requirement: Section-First Retrieval

Paper Q&A SHALL prioritize requested semantic sections and explicitly requested numbered sections before generic document-wide chunks.

#### Scenario: User asks about a compact parsed numbered subsection

- **GIVEN** the parsed paper text contains a compact numbered heading such as `3.2.ALVTSFramework`
- **WHEN** the user asks to explain `第 3.2 节`
- **THEN** retrieved evidence includes content from that compact heading through the next same-or-higher-level numbered heading before generic top-k chunks
- **AND** evidence metadata records the requested section number and matched compact heading.
