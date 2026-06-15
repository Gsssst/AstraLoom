## MODIFIED Requirements

### Requirement: Research Scout prefers arXiv PDF candidates with enrichment
Research Scout SHALL prefer arXiv PDF-backed candidates while using external scholarly providers to enrich metadata and evaluations.

#### Scenario: Research Scout searches for papers
- **WHEN** Research Scout performs scholarly discovery
- **THEN** it uses arXiv-first enriched discovery
- **AND** candidate cards expose PDF availability, enrichment provenance, venue, institution, and citation signals when available.

#### Scenario: Candidate metadata is enriched
- **WHEN** a candidate has venue or institution metadata from Semantic Scholar or OpenAlex
- **THEN** the UI shows the metadata source so the user can distinguish confirmed provider metadata from unknown fields.

#### Scenario: Tool trace describes discovery source
- **WHEN** Research Scout emits tool execution trace metadata
- **THEN** the search step summary indicates that arXiv PDF results were prioritized and enriched with Semantic Scholar/OpenAlex metadata.
