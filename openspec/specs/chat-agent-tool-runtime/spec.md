# chat-agent-tool-runtime Specification

## Purpose
Provide a shared, safe chat tool runtime so chat modes can call backend research tools with typed schemas, bounded execution, observable traces, and explicit confirmation for side effects.

## Requirements
### Requirement: Chat tools are registered with typed schemas
The system SHALL provide a backend chat tool registry where each tool declares a stable name, label, argument schema, side-effect policy, and executor.

#### Scenario: Registered tools expose schemas
- **WHEN** the runtime asks the registry for available tools
- **THEN** it receives UI/model-safe schema summaries for each registered tool
- **AND** the summaries include whether the tool has side effects

#### Scenario: Unknown tool is rejected
- **WHEN** a model or caller requests a tool name that is not registered
- **THEN** the runtime rejects the call
- **AND** the observation lists allowed tool names for debugging

### Requirement: Tool arguments are validated before execution
The runtime SHALL validate tool arguments against each tool's declared schema before calling the executor.

#### Scenario: Invalid arguments do not execute
- **WHEN** a tool call has missing or invalid arguments
- **THEN** the runtime returns a rejected observation
- **AND** the tool executor is not called

### Requirement: Side-effect tools require explicit confirmation
The runtime SHALL block tools that mutate user data unless the request includes an explicit confirmation for that exact tool call.

#### Scenario: Import paper is planned autonomously
- **WHEN** an autonomous tool plan includes `import_paper`
- **THEN** the runtime returns `waiting_confirmation`
- **AND** no paper is imported

#### Scenario: User confirms import paper
- **WHEN** the user confirms a pending `import_paper` action for their own chat session
- **THEN** the runtime executes the import tool
- **AND** returns a completed observation with the imported paper reference

### Requirement: Tool execution emits observable trace events
The runtime SHALL emit structured trace events for planned, running, completed, failed, rejected, skipped, and waiting-confirmation tool states.

#### Scenario: Tool completes successfully
- **WHEN** a tool call runs successfully
- **THEN** the trace includes running and completed events
- **AND** the completed event includes a summary and result count

#### Scenario: Tool waits for confirmation
- **WHEN** a side-effect tool is blocked for confirmation
- **THEN** the trace includes a waiting-confirmation event
- **AND** the frontend can render an action affordance from the event details

### Requirement: Initial research tools are available
The runtime SHALL provide `search_papers`, `search_library`, and `import_paper` as the initial registered tools.

#### Scenario: Search papers
- **WHEN** chat requests a scholarly paper search tool call
- **THEN** `search_papers` returns bounded paper candidates and references without importing them

#### Scenario: Search library
- **WHEN** chat requests a local library search tool call
- **THEN** `search_library` returns bounded local paper references

#### Scenario: Import paper
- **WHEN** chat executes a confirmed `import_paper` tool call
- **THEN** the selected remote paper is added to the user's paper library using existing ingest behavior

### Requirement: Tool runtime is bounded
The runtime SHALL enforce bounded steps, bounded result counts, bounded planner-driven iterations, and graceful failure behavior.

#### Scenario: Planner returns too many calls
- **WHEN** the planner returns more tool calls than the runtime step limit
- **THEN** the runtime executes only the allowed number
- **AND** records a stop reason indicating the limit

#### Scenario: Planner loop reaches round limit
- **WHEN** the planner-driven action/observation loop reaches its configured round limit
- **THEN** the runtime stops additional planning
- **AND** preserves completed observations for the final answer context

#### Scenario: Tool executor fails
- **WHEN** a tool executor raises an exception
- **THEN** the runtime returns a failed observation
- **AND** the chat request continues when a useful partial answer can still be generated

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

### Requirement: Office extraction tools are available
The runtime SHALL provide `extract_docx` and `extract_pptx` as read-only registered chat tools for bounded Office document text extraction.

#### Scenario: Registered Office extraction tools expose schemas
- **WHEN** the chat tool registry returns available tool schemas
- **THEN** the schema list includes `extract_docx` and `extract_pptx`
- **AND** both tools are marked as non-side-effect tools

#### Scenario: Extract Word document text
- **WHEN** chat executes `extract_docx` with a valid `.docx` payload
- **THEN** the tool returns bounded text containing paragraphs, headings when available, and table text
- **AND** the observation includes file type and text length metadata

#### Scenario: Extract PowerPoint slide text
- **WHEN** chat executes `extract_pptx` with a valid `.pptx` payload
- **THEN** the tool returns bounded text grouped by slide number
- **AND** the observation includes slide count and text length metadata

#### Scenario: Office extraction is read-only
- **WHEN** the planner selects `extract_docx` or `extract_pptx`
- **THEN** the runtime executes the tool without confirmation
- **AND** no user library, folder, project, or chat state mutation is performed by the tool itself
