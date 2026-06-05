# arxiv-pdf-mirror-cache Specification

## Purpose
TBD - created by archiving change arxiv-pdf-mirror-cache. Update Purpose after archive.
## Requirements
### Requirement: Configurable mirror fallback
The system SHALL try configured arXiv PDF mirror base URLs in order and SHALL retain the official arXiv PDF host as the final fallback.

#### Scenario: First mirror fails
- **WHEN** the first configured mirror returns an error or invalid PDF response
- **THEN** the service tries the next configured candidate until a valid PDF is received or all candidates fail

### Requirement: Persistent local PDF cache
The system SHALL persist valid downloaded arXiv PDFs in a dedicated local cache directory and SHALL reuse cached files before contacting an upstream host.

#### Scenario: Reader requests an already cached PDF
- **WHEN** a valid cache file exists for the requested arXiv identifier
- **THEN** the reader proxy serves the cached PDF without issuing an upstream HTTP request

### Requirement: Shared cache reuse
The system SHALL use the shared arXiv PDF cache for paper reading, full-text extraction, and background download tasks.

#### Scenario: Full-text extraction follows a reader download
- **WHEN** the reader proxy has already cached a paper PDF and full-text extraction runs later
- **THEN** full-text extraction parses the cached file without downloading the PDF again

### Requirement: PDF download validation
The system SHALL reject invalid arXiv identifiers and SHALL persist only responses with PDF file signatures.

#### Scenario: Upstream responds with HTML error content
- **WHEN** a candidate PDF URL returns content that does not begin with a PDF signature
- **THEN** the service does not cache the response and tries the next candidate

