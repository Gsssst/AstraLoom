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
