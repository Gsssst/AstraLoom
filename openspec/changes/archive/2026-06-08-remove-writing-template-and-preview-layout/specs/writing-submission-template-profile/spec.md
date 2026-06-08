## MODIFIED Requirements

### Requirement: Writing projects can bind a submission profile
The system SHALL bind target venue/year and inspected template metadata to a writing project.

#### Scenario: User removes bound template profile
- **GIVEN** a writing project has a bound submission template profile
- **WHEN** the user removes the template
- **THEN** the project no longer reports a bound submission profile
- **AND** LaTeX compile settings are reset to a safe single-column article configuration.

### Requirement: Frontend exposes template-aware submission guidance
The frontend SHALL let users inspect/bind a submission profile from the writing workbench.

#### Scenario: User can remove unwanted template
- **GIVEN** a selected writing project has a bound template profile
- **WHEN** the user views template settings
- **THEN** they can remove the template binding without editing database state manually.
