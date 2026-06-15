## ADDED Requirements

### Requirement: Scholarly discovery supports arXiv-first enrichment
The scholarly search service SHALL support an arXiv-first enriched discovery mode for workflows that need reliable PDFs.

#### Scenario: arXiv returns candidates
- **WHEN** discovery is called with the arXiv-enriched source
- **THEN** arXiv results are returned first
- **AND** each arXiv result keeps its arXiv id and PDF URL when available.

#### Scenario: matching metadata exists in other providers
- **WHEN** Semantic Scholar or OpenAlex returns a matching paper by arXiv id, DOI, or normalized title
- **THEN** the arXiv candidate is enriched with venue, citation count, DOI, source URL, institutions, and metadata provenance where available
- **AND** the result still identifies as an arXiv candidate for PDF-first workflows.

#### Scenario: enrichment providers fail or do not match
- **WHEN** enrichment fails or no match is available
- **THEN** the arXiv candidate still appears with arXiv metadata
- **AND** unavailable venue or institution fields remain unknown rather than fabricated.

### Requirement: arXiv feed metadata is preserved
arXiv search results SHALL preserve useful feed metadata for downstream candidate evidence.

#### Scenario: arXiv feed includes journal reference or comments
- **WHEN** an arXiv entry includes DOI, journal reference, comments, or categories
- **THEN** those fields are included in candidate metadata and provenance.
