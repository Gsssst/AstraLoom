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

### Requirement: Export readiness reflects template profile state

The system SHALL include submission profile state in writing project export readiness.

#### Scenario: User has not attached official template

- **GIVEN** a writing project has only a structure template
- **WHEN** export readiness is loaded
- **THEN** the readiness result warns that official submission formatting has not been verified

### Requirement: Frontend exposes template-aware submission guidance

The frontend SHALL let users inspect/bind a submission profile from the writing workbench.

#### Scenario: User configures submission target

- **GIVEN** a selected writing project
- **WHEN** the user enters venue/year and uploads a template file
- **THEN** they see inspection results and can bind the profile to the project
