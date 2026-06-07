## MODIFIED Requirements

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
