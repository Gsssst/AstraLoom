# research-code-project-generation Specification

## Purpose
Generate structured, inspectable, and downloadable experiment project packages for Research Idea Proposals instead of limiting implementation output to a single code snippet.

## Requirements
### Requirement: Research Idea Generates Structured Experiment Project
The system SHALL generate a structured experiment project package for a Research Idea instead of exposing only a single generated code string.

#### Scenario: Project package generated for an owned Idea
- **WHEN** an authenticated owner requests code generation for a Research Idea
- **THEN** the response includes the Idea id, framework, project name, summary, setup instructions, run commands, entrypoints, safety notes, and a list of generated files with path, language, purpose, and content.

#### Scenario: Generated output is persisted
- **WHEN** a project package is generated successfully
- **THEN** the package manifest is persisted on the Research Idea
- **AND** the Idea remains compatible with legacy consumers by retaining a representative generated code string.

#### Scenario: Model output is malformed
- **WHEN** the language model does not return a valid package manifest
- **THEN** the system returns and persists a conservative fallback project package derived from the Proposal and experiment plan.

### Requirement: Research Code Project Files Are Safe And Bounded
The system SHALL validate generated project files before persisting or downloading them.

#### Scenario: File paths are unsafe
- **WHEN** generated files contain absolute paths, parent traversal, empty paths, or duplicate paths
- **THEN** the system normalizes or rejects those entries so the persisted package contains only safe relative paths.

#### Scenario: Generated package is too large
- **WHEN** generated files exceed the supported file count or per-file size
- **THEN** the system bounds the manifest to a manageable package and records available safe files only.

### Requirement: Research Code Project Can Be Inspected And Downloaded
The research project page SHALL let users inspect generated experiment project packages as browsable projects and SHALL let users download the validated package archive.

#### Scenario: User views generated project package
- **WHEN** a Proposal has a generated project package
- **THEN** the page shows project metadata, setup instructions, run commands, entrypoints, safety notes, file tree, and a selected file preview.

#### Scenario: User browses generated project files
- **WHEN** a generated project package contains multiple files across folders
- **THEN** the page presents a folder-aware file tree and lets the user select a file without leaving the Proposal context.

#### Scenario: User previews a generated file
- **WHEN** the user selects a generated project file
- **THEN** the page shows the file path, language, purpose, line count, content preview, and a copy action for that file.

#### Scenario: User copies a run command
- **WHEN** a generated project package includes run commands
- **THEN** the page presents those commands with copy actions and wraps long commands within the available layout.

#### Scenario: User downloads generated project package
- **WHEN** a Proposal has a generated project package and the user selects download
- **THEN** the backend streams a zip archive containing the validated package files.

#### Scenario: Existing legacy code is present
- **WHEN** a Proposal has legacy generated code but no project package
- **THEN** the page can still show the legacy code and offer regeneration as a structured project package.

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
