## MODIFIED Requirements

### Requirement: Paper full text loading uses available PDF parsers
The paper AI backend SHALL extract and persist paper full text with an installed PDF parser before answering section-specific questions. Concurrent requests for the same missing full text SHALL share one loading task, and timed-out foreground waits SHALL allow that task to finish in the background.

#### Scenario: Paper detail preload and question overlap
- **WHEN** paper detail preload and a paper question request full text for the same paper at the same time
- **THEN** the backend performs one shared PDF loading task and persists the extracted text

#### Scenario: Missing PDF path is recovered for arXiv paper
- **GIVEN** an arXiv paper has full text but no persisted `pdf_path`
- **AND** its PDF is available in the shared arXiv PDF cache or can be downloaded through configured PDF sources
- **WHEN** structured PDF parsing is requested
- **THEN** the backend resolves and persists `pdf_path`
- **AND** structured parsing uses the recovered local PDF path

#### Scenario: PDF path cannot be recovered
- **GIVEN** a paper has no local `pdf_path`
- **AND** no arXiv PDF can be resolved for the paper
- **WHEN** structured PDF parsing is requested
- **THEN** the API returns an actionable failure status that explains why parsing cannot continue

#### Scenario: Parser health is visible
- **WHEN** an administrator inspects PDF structured parsing status
- **THEN** the backend exposes configured parser backend and available parser capabilities such as lightweight parser, Docling, command parser, and HuggingFace mirror/cache settings

#### Scenario: Advanced parser is available
- **WHEN** a configured advanced parser such as Docling or a command parser returns usable table blocks
- **THEN** the backend persists those blocks as structured evidence before falling back to lightweight table extraction
