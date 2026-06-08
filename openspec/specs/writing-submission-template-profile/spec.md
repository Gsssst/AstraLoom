# writing-submission-template-profile Specification

## Purpose
Allow writing projects to attach venue/year targets and inspected official LaTeX template metadata so export readiness can distinguish structure guidance from verified submission formatting.
## Requirements
### Requirement: Writing projects can inspect submission templates

The system SHALL inspect user-uploaded LaTeX submission template files.

#### Scenario: User uploads a venue template package

- **GIVEN** a user has a writing project
- **WHEN** they upload a `.tex`, `.cls`, `.sty`, or `.zip` template file
- **THEN** the system returns inspected metadata including document class, class/style files, package hints, and warnings

### Requirement: Writing projects can bind a submission profile

The system SHALL bind target venue/year and inspected template metadata to a writing project.

#### Scenario: User binds CVPR template profile

- **GIVEN** the user owns or can edit a writing project
- **WHEN** they submit venue, year, and template inspection data
- **THEN** the project metadata includes a submission profile visible in later project reads

#### Scenario: Bound template seeds compile settings
- **GIVEN** the user owns or can edit a writing project
- **WHEN** they bind a submission template profile with detected document class and packages
- **THEN** the project metadata includes LaTeX compile settings that can be used by preview and export rendering.

#### Scenario: User removes bound template profile
- **GIVEN** a writing project has a bound submission template profile
- **WHEN** the user removes the template
- **THEN** the project no longer reports a bound submission profile
- **AND** LaTeX compile settings are reset to a safe single-column article configuration.

### Requirement: Export readiness reflects template profile state

The system SHALL include submission profile state in writing project export readiness.

#### Scenario: User has not attached official template

- **GIVEN** a writing project has only a structure template
- **WHEN** export readiness is loaded
- **THEN** the readiness result warns that official submission formatting has not been verified

#### Scenario: Export uses configured compile layout
- **GIVEN** a writing project has LaTeX compile settings
- **WHEN** the user exports or previews LaTeX
- **THEN** the generated document skeleton reflects those settings.

### Requirement: Frontend exposes template-aware submission guidance

The frontend SHALL let users inspect/bind a submission profile from the writing workbench.

#### Scenario: User configures submission target

- **GIVEN** a selected writing project
- **WHEN** the user enters venue/year and uploads a template file
- **THEN** they see inspection results and can bind the profile to the project

#### Scenario: User chooses manuscript compile layout
- **GIVEN** a selected writing project
- **WHEN** the user chooses single-column, double-column, or template-informed layout
- **THEN** later manuscript preview/export actions use that layout.

#### Scenario: User can remove unwanted template
- **GIVEN** a selected writing project has a bound template profile
- **WHEN** the user views template settings
- **THEN** they can remove the template binding without editing database state manually.

### Requirement: Template profile binding returns updated project safely
The system SHALL return the updated writing project after binding a submission template profile without triggering asynchronous lazy-load failures.

#### Scenario: User binds template to project with sections
- **WHEN** a user binds venue/year and inspected template metadata to a writing project that has sections
- **THEN** the backend response includes the updated project and sections
- **AND** serialization does not attempt unsupported async lazy loading.
