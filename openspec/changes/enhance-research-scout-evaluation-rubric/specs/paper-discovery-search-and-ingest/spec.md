## MODIFIED Requirements

### Requirement: Paper discovery candidates expose reusable scholarly metadata
Paper discovery candidate payloads SHALL include enough metadata for downstream chat, library, and project workflows to render, ingest, and compare papers without reparsing prose.

#### Scenario: Research Scout consumes candidate metadata
- **WHEN** scholarly discovery returns paper candidates to Research Scout
- **THEN** each candidate may include venue, citation count, source URL, PDF URL, remote identifiers, authors, abstract, and evaluation metadata when available
- **AND** missing optional metadata remains absent or explicitly unknown rather than fabricated.
