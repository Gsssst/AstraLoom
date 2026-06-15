## MODIFIED Requirements

### Requirement: Scholarly discovery supports arXiv-first enrichment
The scholarly search service SHALL support an arXiv-first enriched discovery mode for workflows that need reliable PDFs.

#### Scenario: arXiv results need affiliation enrichment
- **WHEN** arXiv-enriched discovery returns PDF-backed candidates
- **THEN** the service attempts bounded first-page affiliation extraction for top candidates
- **AND** merges extracted institutions with Semantic Scholar/OpenAlex metadata when evidence is available.
