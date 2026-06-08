## ADDED Requirements

### Requirement: LaTeX Preview Degrades Gracefully Without Compiler
The manuscript workbench SHALL provide useful LaTeX diagnostics when `pdflatex` is unavailable.

#### Scenario: Compiler is unavailable
- **WHEN** a user runs section or manuscript LaTeX preview in an environment without `pdflatex`
- **THEN** the preview response identifies that the compiler is unavailable
- **AND** the response includes source-level diagnostics instead of only a hard failure.

### Requirement: Section Editing Does Not Jump On Every Keystroke
The manuscript section editor SHALL avoid full workbench rerenders and layout jumps while users type.

#### Scenario: User types in a section body
- **WHEN** the user edits the LaTeX source
- **THEN** the input updates locally without saving on every keystroke
- **AND** persistence is debounced or flushed on an intentional boundary.

#### Scenario: User runs a section action after typing
- **WHEN** the user triggers preview, citation check, quality check, or a section AI action
- **THEN** the action uses the latest visible draft content.
