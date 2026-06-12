## MODIFIED Requirements

### Requirement: Visual Evidence References
Paper Q&A SHALL expose visual evidence references with enough metadata for the frontend to display, preview, and navigate them.

#### Scenario: Answer includes visual evidence
- **WHEN** a paper Q&A response uses a visual asset
- **THEN** the response metadata includes the asset id, evidence type, page number, optional bbox, caption, thumbnail or image path, visual summary snippet, and parser/source metadata
- **AND** figure/table visual references prefer focused crop assets over full-page images when crop metadata is available.
