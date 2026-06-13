## ADDED Requirements

### Requirement: Direct imports immediately enter processing
The system SHALL submit every newly created paper from direct import endpoints to the automatic paper processing pipeline immediately after the paper is committed.

#### Scenario: BibTeX import creates papers
- **WHEN** a BibTeX import creates one or more new paper records
- **THEN** each new paper SHALL be submitted to `process_paper_pipeline` without waiting for the periodic reconciler

#### Scenario: Zotero import creates papers
- **WHEN** a Zotero CSV import creates one or more new paper records
- **THEN** each new paper SHALL be submitted to `process_paper_pipeline` without waiting for the periodic reconciler

### Requirement: Queued processing is visible
The system SHALL persist processing metadata when a paper is submitted to the automatic processing pipeline so the paper is not displayed as merely待处理 while backend work is queued.

#### Scenario: Processing task submitted
- **WHEN** a new paper is submitted to `process_paper_pipeline`
- **THEN** the paper processing labels SHALL expose queued or running processing state for automatic artifacts until the worker completes or fails them

### Requirement: PDF extraction persistence is robust
The system SHALL sanitize PDF extracted text and structured metadata before storing them and SHALL keep reconciliation running when one paper fails.

#### Scenario: Extracted PDF contains invalid control characters
- **WHEN** a PDF parser returns text or metadata containing NUL bytes
- **THEN** the system SHALL remove invalid bytes before writing to PostgreSQL

#### Scenario: One paper processing fails in a batch
- **WHEN** one paper fails during reconciliation
- **THEN** the system SHALL roll back that failed transaction, record the failure, and continue processing later selected papers

### Requirement: Scheduled processing is repeatable
The system SHALL run repeated Celery paper-processing tasks without reusing async database connections from closed event loops.

#### Scenario: Reconciler runs repeatedly in one worker process
- **WHEN** `reconcile_paper_processing` runs more than once in the same Celery worker process
- **THEN** each run SHALL release async database connections before the worker processes the next run

### Requirement: Visual processing completion requires OCR-ready evidence
The system SHALL consider visual evidence processing complete only when required table OCR and visual summaries are available for paper Q&A.

#### Scenario: Cached visual items still lack table OCR
- **WHEN** a paper has cached visual evidence items with one or more tables lacking OCR markdown
- **THEN** automatic processing SHALL keep the visual evidence step incomplete instead of marking it completed

#### Scenario: Visual OCR cannot run because assets are unavailable
- **WHEN** a table lacks OCR and no page or crop asset is available for model OCR
- **THEN** the system SHALL expose a blocking visual evidence error explaining the missing OCR asset prerequisite
