## MODIFIED Requirements

### Requirement: Section-First Retrieval

Paper Q&A SHALL prioritize requested semantic sections and explicitly requested numbered sections before generic document-wide chunks.

#### Scenario: User asks about Introduction

- **GIVEN** the full text contains an Introduction section
- **WHEN** the user asks to explain the Introduction
- **THEN** retrieved evidence comes from the Introduction section before falling back to document-wide chunks.

#### Scenario: User asks about a numbered subsection

- **GIVEN** the parsed paper text contains a numbered heading such as `3.2 Retrieval Module`
- **WHEN** the user asks to explain `第 3.2 节` or `Section 3.2`
- **THEN** retrieved evidence includes content from that heading through the next same-or-higher-level numbered heading before generic top-k chunks
- **AND** evidence metadata records the requested section number and matched heading.

#### Scenario: Requested numbered subsection is missing from parsed text

- **GIVEN** the user asks for `第 3.2 节`
- **AND** the parsed paper text does not contain a matching numbered heading
- **WHEN** the AI builds its answer context
- **THEN** the evidence plan includes a warning that the requested numbered section was not located
- **AND** the assistant is instructed to disclose the exact missing section rather than implying the entire paper is unavailable.
