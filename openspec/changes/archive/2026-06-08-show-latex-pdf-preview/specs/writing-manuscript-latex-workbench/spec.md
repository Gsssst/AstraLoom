## MODIFIED Requirements

### Requirement: LaTeX Preview Checks Are Available
The system SHALL provide compile/preview checks for the active section and assembled manuscript.

#### Scenario: Preview active section
- **WHEN** the user requests preview for the active section
- **THEN** the system compiles or validates the section inside a minimal LaTeX document wrapper
- **AND** returns success status, warnings, errors, and compiler log details
- **AND** when compilation produces a PDF, returns a PDF preview URL for the compiled section.

#### Scenario: Preview whole manuscript
- **WHEN** the user requests preview for the whole manuscript
- **THEN** the system checks the assembled LaTeX export and returns diagnostics
- **AND** when compilation produces a PDF, returns a PDF preview URL for the compiled manuscript.

#### Scenario: LaTeX compiler is unavailable
- **WHEN** the runtime does not have a LaTeX compiler available
- **THEN** the UI shows a clear compiler-unavailable diagnostic instead of failing silently
- **AND** no PDF preview is shown.

#### Scenario: Compile succeeds with warnings
- **WHEN** LaTeX compilation succeeds but emits warnings
- **THEN** the UI shows the warning diagnostics and still displays the compiled PDF preview.
