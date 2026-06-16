## ADDED Requirements

### Requirement: Library action tools are available
The runtime SHALL provide `read_pdf`, `add_to_folder`, and `create_research_project` as registered chat tools in addition to the initial research tools.

#### Scenario: Registered library action tools expose schemas
- **WHEN** the chat tool registry returns available tool schemas
- **THEN** the schema list includes `read_pdf`, `add_to_folder`, and `create_research_project`
- **AND** the schema list marks `add_to_folder` and `create_research_project` as side-effect tools

#### Scenario: Read local paper evidence
- **WHEN** chat executes `read_pdf` for a local paper the user can access
- **THEN** the tool returns bounded paper evidence from full text chunks when available
- **AND** the observation states whether the evidence came from full text or abstract-only metadata

#### Scenario: Add paper to folder requires confirmation
- **WHEN** an autonomous tool plan requests `add_to_folder`
- **THEN** the runtime returns `waiting_confirmation`
- **AND** no folder membership is changed until the user confirms the exact tool arguments

#### Scenario: Create research project requires confirmation
- **WHEN** an autonomous tool plan requests `create_research_project`
- **THEN** the runtime returns `waiting_confirmation`
- **AND** no research project is created until the user confirms the exact tool arguments

#### Scenario: Confirmed folder action mutates user library
- **WHEN** the user confirms a pending `add_to_folder` action for their own chat session
- **THEN** the selected local papers are added to the selected folder using existing folder membership behavior
- **AND** the completed observation reports added and skipped counts

#### Scenario: Confirmed project action mutates research projects
- **WHEN** the user confirms a pending `create_research_project` action for their own chat session
- **THEN** a research project is created for the current user with the supplied metadata and local paper IDs
- **AND** the completed observation returns the created project reference
