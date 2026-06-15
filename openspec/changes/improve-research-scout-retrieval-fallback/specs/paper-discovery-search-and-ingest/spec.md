## ADDED Requirements

### Requirement: Paper discovery supports arXiv-preferred broad scholarly fallback
The system SHALL support paper discovery flows that prefer arXiv/PDF-backed results while allowing broad scholarly providers to fill candidate gaps.

#### Scenario: arXiv-preferred search returns too few papers
- **WHEN** a paper discovery workflow requests arXiv-preferred results and the arXiv-backed result set is below the requested target
- **THEN** the workflow can broaden retrieval to configured scholarly providers
- **AND** returns deduplicated candidates from the broader set without blocking on a single provider.

#### Scenario: broad result lacks arXiv PDF
- **WHEN** a fallback paper candidate comes from Semantic Scholar, OpenAlex, or Google Scholar without an arXiv PDF
- **THEN** the response preserves the actual provider and PDF availability metadata
- **AND** downstream import actions resolve the candidate through its provider-specific identifier or URL.
