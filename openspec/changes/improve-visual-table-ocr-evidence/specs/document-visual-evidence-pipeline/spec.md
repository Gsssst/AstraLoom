## MODIFIED Requirements

### Requirement: Crop-Level Vision Model Adapter
The system SHALL call an image-capable model only for local crops or page assets selected from parser-located candidates, unless a deployment explicitly configures a different external parser command.

#### Scenario: Crop needs visual understanding
- **WHEN** a figure, chart, architecture diagram, or low-confidence table crop/page asset is selected for vision analysis
- **THEN** the vision adapter receives the crop or page image and returns strict structured data including kind, OCR text or markdown when applicable, summary, key facts, confidence, uncertainty notes, and model/provider metadata.

#### Scenario: Parser table evidence is incomplete
- **WHEN** a table-like visual evidence item has a local page or crop asset and parser markdown is missing, sparse, generic, or low fidelity
- **THEN** the visual evidence pipeline sends each eligible asset to the configured system model, unless a positive deployment cap has been configured and already reached
- **AND** the persisted item stores OCR-enhanced table markdown, OCR text, key facts, confidence, and uncertainty metadata when the model returns usable structured data.

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
- **THEN** the system persists ready evidence metadata, including OCR-enhanced visual table markdown when available, and makes it available to later Q&A turns without rerunning extraction.
