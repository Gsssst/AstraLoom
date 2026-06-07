## ADDED Requirements

### Requirement: Research Code Project Versions Are Preserved
The system SHALL preserve a version snapshot each time a structured experiment project package is generated for a Research Idea.

#### Scenario: First project version is generated
- **WHEN** an authenticated owner generates a structured code project for an Idea with no prior code project versions
- **THEN** the system stores version `1` with the normalized project manifest and representative code
- **AND** the Idea latest `generated_code_project` remains populated for existing consumers

#### Scenario: Later project version is generated
- **WHEN** an authenticated owner regenerates a structured code project for an Idea with existing code project versions
- **THEN** the system stores the next monotonically increasing version number
- **AND** previous version snapshots remain retrievable

### Requirement: Research Code Project Version APIs Are Available
The backend SHALL expose owner-scoped APIs to list code project versions, retrieve a version manifest, and compare two versions for a Research Idea.

#### Scenario: User lists versions for an owned Idea
- **WHEN** an authenticated owner requests code project versions for an Idea
- **THEN** the response lists available versions with id, version number, project name, framework, summary, file count, and creation time.

#### Scenario: User retrieves a version manifest
- **WHEN** an authenticated owner requests a specific code project version
- **THEN** the response returns the version metadata and stored project manifest.

#### Scenario: User compares two versions
- **WHEN** an authenticated owner compares two versions of the same Idea
- **THEN** the response includes file-level statuses for added, removed, modified, and unchanged files.

#### Scenario: User requests another user's version
- **WHEN** an authenticated user requests versions or comparisons for an Idea they do not own
- **THEN** the system returns a not-found response without exposing version contents.

### Requirement: Research Code Project Version Diff Is Inspectable
The research project page SHALL let users inspect saved code project versions and compare two versions within the Proposal context.

#### Scenario: User switches project version
- **WHEN** a Proposal has saved code project versions
- **THEN** the project browser shows a version selector and lets the user preview an older version without replacing the latest package.

#### Scenario: User views version diff summary
- **WHEN** a user compares two saved versions
- **THEN** the page shows counts and file rows for added, removed, modified, and unchanged files.

#### Scenario: User opens modified file diff
- **WHEN** a compared file is modified
- **THEN** the page shows a compact diff preview for that file while preserving the normal file browser.

#### Scenario: No saved versions exist
- **WHEN** a Proposal has a generated latest package but no saved version rows
- **THEN** the page continues to show the latest project package and explains that version history starts after the next generation.
