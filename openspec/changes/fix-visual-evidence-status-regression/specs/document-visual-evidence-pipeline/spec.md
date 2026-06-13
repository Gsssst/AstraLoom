## MODIFIED Requirements

### Requirement: Document Visual Evidence Schema
The system SHALL normalize PDF-derived visual and table evidence into a versioned, bounded schema that can be reused by paper Q&A and chat PDF attachments.

#### Scenario: Parser returns visual evidence
- **WHEN** a PDF parser or vision adapter returns a figure, chart, table, page render, OCR, or formula evidence item
- **THEN** the system stores a normalized item with page, optional bbox, kind, caption, asset path or thumbnail path when available, parser/source, confidence, status, and extracted text, markdown, or summary when available.

#### Scenario: Vision corrects parser type
- **WHEN** vision OCR determines that a parser table candidate is actually a non-table visual or text element
- **THEN** the system preserves the parser kind for traceability
- **AND** uses the corrected effective kind for visual/table readiness counts and missing OCR checks.

### Requirement: Asynchronous Visual Evidence Processing
The system SHALL run visual evidence extraction and crop-level OCR as bounded asynchronous work that does not block the paper library or chat answer generation path.

#### Scenario: Extraction job completes
- **WHEN** a visual evidence job finishes successfully
- **THEN** the system persists ready evidence metadata, including OCR-enhanced visual table markdown when available, and makes it available to later Q&A turns without rerunning extraction.

#### Scenario: Non-table correction completes a candidate
- **WHEN** a parser table candidate receives ready OCR output whose effective kind is non-table and has OCR text or summary
- **THEN** the system does not count that candidate as missing table OCR
- **AND** the paper can be marked visual-evidence ready if no actual table, visual summary, or blocking asset errors remain incomplete.

#### Scenario: Stale asset error is retried
- **WHEN** existing visual evidence metadata contains an asset rendering error and forced extraction is run after the runtime dependency is available
- **THEN** the system replaces the stale failed item metadata with newly rendered evidence assets when rendering succeeds
- **AND** clears the blocking visual evidence error from the readiness status.
