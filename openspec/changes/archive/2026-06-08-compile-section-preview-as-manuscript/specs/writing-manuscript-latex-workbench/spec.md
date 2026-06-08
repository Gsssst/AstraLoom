## MODIFIED Requirements

### Requirement: LaTeX Preview Checks Are Available
The system SHALL provide compile/preview checks for the active section and assembled manuscript.

#### Scenario: Preview active section as assembled manuscript
- **WHEN** the user requests preview from the active section editor
- **THEN** the system compiles the full manuscript document
- **AND** replaces the matching manuscript section with the active editor draft before compilation
- **AND** returns success status, warnings, errors, and compiler log details
- **AND** when compilation produces a PDF, returns a PDF preview URL for the compiled manuscript
- **AND** identifies that the PDF scope is the manuscript.

#### Scenario: Preview active section draft without matching persisted section
- **WHEN** the user requests preview from the active section editor and the section id is not found in the project sections
- **THEN** the system includes the active section draft in the assembled manuscript preview instead of compiling only the draft in isolation.
