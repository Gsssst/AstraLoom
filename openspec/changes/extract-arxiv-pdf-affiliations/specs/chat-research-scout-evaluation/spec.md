## MODIFIED Requirements

### Requirement: Research Scout prefers arXiv PDF candidates with enrichment
Research Scout SHALL prefer arXiv PDF-backed candidates while using external scholarly providers and PDF first-page evidence to enrich metadata and evaluations.

#### Scenario: PDF-derived affiliations are available
- **WHEN** a Research Scout candidate has institutions extracted from the arXiv PDF first page
- **THEN** candidate cards show that the institution evidence came from `PDF 首页`
- **AND** users can inspect a short evidence cue instead of seeing an unsupported affiliation claim.
