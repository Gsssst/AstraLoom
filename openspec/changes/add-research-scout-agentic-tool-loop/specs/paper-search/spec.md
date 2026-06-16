## ADDED Requirements

### Requirement: Paper search accepts structured venue constraints
Paper search services SHALL accept structured venue constraints for supported providers and SHALL preserve venue match metadata in normalized results.

#### Scenario: Search with venue filter
- **WHEN** a paper discovery workflow searches with `venue=CVPR`
- **THEN** supported venue-aware providers receive that venue constraint
- **AND** results include venue match status and provenance when available.

#### Scenario: Provider does not support venue filter
- **WHEN** a provider cannot apply a venue filter directly
- **THEN** the system records that venue was not provider-filtered
- **AND** downstream filtering must not treat the provider result as venue-confirmed without evidence.

### Requirement: Paper search applies year constraints during provider calls
Paper search services SHALL pass structured year filters into remote provider calls whenever the provider supports them and SHALL post-filter known years when a provider cannot filter remotely.

#### Scenario: Search with year range
- **WHEN** a paper discovery workflow searches with `year_from=2025` and `year_to=2026`
- **THEN** arXiv, Semantic Scholar, OpenAlex, and optional Google Scholar calls receive the year range where supported
- **AND** results with known years outside the range are excluded before ranking.

#### Scenario: Provider returns unknown year
- **WHEN** a provider returns a candidate without a publication year
- **THEN** the normalized result marks the year as unknown
- **AND** downstream hard-constraint filtering decides whether to exclude or label it unverified.
