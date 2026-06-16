## ADDED Requirements

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
