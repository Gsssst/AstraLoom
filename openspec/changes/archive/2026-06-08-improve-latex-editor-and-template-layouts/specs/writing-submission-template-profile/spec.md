## MODIFIED Requirements

### Requirement: Writing projects can bind a submission profile
The system SHALL bind target venue/year and inspected submission template metadata to a writing project.

#### Scenario: Bound template seeds compile settings
- **GIVEN** the user owns or can edit a writing project
- **WHEN** they bind a submission template profile with detected document class and packages
- **THEN** the project metadata includes LaTeX compile settings that can be used by preview and export rendering.

### Requirement: Frontend exposes template-aware submission guidance
The frontend SHALL let users inspect/bind a submission profile from the writing workbench.

#### Scenario: User chooses manuscript compile layout
- **GIVEN** a selected writing project
- **WHEN** the user chooses single-column, double-column, or template-informed layout
- **THEN** later manuscript preview/export actions use that layout.

### Requirement: Export readiness reflects template profile state
The system SHALL include submission profile state in writing project export readiness.

#### Scenario: Export uses configured compile layout
- **GIVEN** a writing project has LaTeX compile settings
- **WHEN** the user exports or previews LaTeX
- **THEN** the generated document skeleton reflects those settings.
