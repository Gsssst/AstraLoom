## ADDED Requirements

### Requirement: Document Visual Evidence Schema
The system SHALL normalize PDF-derived visual and table evidence into a versioned, bounded schema that can be reused by paper Q&A and chat PDF attachments.

#### Scenario: Parser returns visual evidence
- **WHEN** a PDF parser or vision adapter returns a figure, chart, table, page render, OCR, or formula evidence item
- **THEN** the system stores a normalized item with page, optional bbox, kind, caption, asset path or thumbnail path when available, parser/source, confidence, status, and extracted text, markdown, or summary when available.

#### Scenario: Evidence exceeds bounds
- **WHEN** parser output contains more pages, assets, or text than the configured evidence limits
- **THEN** the system stores only the bounded subset and records limit metadata without failing the PDF processing request.

### Requirement: Parser-First Visual Evidence Extraction
The system SHALL locate visual and table evidence with deterministic parser adapters before invoking any vision-model OCR or understanding adapter.

#### Scenario: Docling is available
- **WHEN** a local PDF is processed and the Docling adapter is available
- **THEN** the system uses Docling output to locate typed text, table, picture, figure, formula, caption, page, and bbox candidates before falling back to lighter parsers.

#### Scenario: Optional parser is unavailable
- **WHEN** the configured advanced parser is missing, fails, or returns no usable evidence
- **THEN** the system falls back to the next available parser and records parser health instead of failing normal paper Q&A.

### Requirement: Crop-Level Vision Model Adapter
The system SHALL call an image-capable model only for bounded local crops selected from parser-located candidates, unless a deployment explicitly configures a different external parser command.

#### Scenario: Crop needs visual understanding
- **WHEN** a figure, chart, architecture diagram, or low-confidence table crop is selected for vision analysis
- **THEN** the vision adapter receives the crop image and returns strict structured data including kind, OCR text or markdown when applicable, summary, key facts, confidence, and model/provider metadata.

#### Scenario: Whole PDF would be sent to a vision model
- **WHEN** visual evidence extraction runs under default settings
- **THEN** the system does not send the entire PDF or all page screenshots to a vision model as the primary extraction strategy.

### Requirement: Asynchronous Visual Evidence Processing
The system SHALL run visual evidence extraction and crop-level OCR as bounded asynchronous work that does not block the paper library or chat answer generation path.

#### Scenario: Evidence is missing during Q&A
- **WHEN** a user asks a question before visual evidence processing is ready
- **THEN** the system may enqueue or recommend visual evidence extraction but answers only from currently ready evidence.

#### Scenario: Extraction job completes
- **WHEN** a visual evidence job finishes successfully
- **THEN** the system persists ready evidence metadata and makes it available to later Q&A turns without rerunning extraction.

### Requirement: Uploaded PDF Chat Uses Shared Evidence
The chat system SHALL use the shared document visual evidence pipeline for uploaded PDFs so image and table evidence can be available to the conversation beyond plain extracted text.

#### Scenario: User uploads a PDF with tables or figures
- **WHEN** a chat attachment is a PDF and bounded evidence extraction succeeds
- **THEN** the chat context and message references include ready table or visual evidence with page and asset metadata where available.

#### Scenario: Uploaded PDF visual evidence is unavailable
- **WHEN** a chat PDF cannot produce ready visual evidence
- **THEN** the assistant context discloses that only text extraction is available and avoids claiming details from unseen figures or tables.

### Requirement: Private Asset Access
The system SHALL serve generated visual evidence assets through authenticated application routes or private cache paths rather than exposing private PDF-derived images as public repository files.

#### Scenario: Frontend requests an evidence asset
- **WHEN** an authenticated user opens a visual evidence preview for a paper or uploaded PDF they can access
- **THEN** the backend returns the thumbnail or crop through an authorized route.

#### Scenario: Unauthorized asset request
- **WHEN** a user requests a visual evidence asset for a paper or attachment they cannot access
- **THEN** the backend rejects the request without revealing the private asset path.
