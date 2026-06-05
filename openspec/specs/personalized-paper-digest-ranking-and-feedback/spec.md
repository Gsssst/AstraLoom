# personalized-paper-digest-ranking-and-feedback Specification

## Purpose
TBD - created by archiving change personalized-paper-digest-ranking-and-feedback. Update Purpose after archive.
## Requirements
### Requirement: Digest candidate discovery uses multiple scholarly providers
The system SHALL retrieve digest candidates through the configured scholarly provider aggregator and SHALL deduplicate canonical papers across providers and subscription keywords before ranking.

#### Scenario: Same paper appears from multiple sources
- **WHEN** multiple providers or keywords return the same canonical paper
- **THEN** the digest contains one recommendation card for that paper

### Requirement: Scheduled digests use precise publication freshness when available
The system SHALL preserve provider publication timestamps and SHALL use a bounded freshness window for scheduled digest candidates when a precise timestamp is available.

#### Scenario: Dated paper is outside the freshness window
- **WHEN** a scheduled digest candidate has a precise publication timestamp older than the configured freshness window
- **THEN** the system excludes that candidate from the scheduled digest

#### Scenario: Manual test digest is requested
- **WHEN** a user triggers an explicit test digest
- **THEN** the system can include relevant older candidates so the user can validate the delivery and recommendation experience

### Requirement: Digest ranking uses explainable user preference signals
The system SHALL rank digest candidates using subscription keywords, active research-project keywords, saved or read-paper interest signals, publication freshness, and source diversity, and SHALL persist visible recommendation reasons.

#### Scenario: Candidate matches an active research direction
- **WHEN** a candidate overlaps with the user's active research-project keywords
- **THEN** the system applies a bounded ranking boost and records an explanatory reason

### Requirement: Users can provide digest recommendation feedback
The digest inbox SHALL allow an authenticated user to record `interested`, `later`, or `dismissed` feedback for an individual recommendation.

#### Scenario: User marks paper as not interested
- **WHEN** the user marks a digest recommendation as `dismissed`
- **THEN** the system stores the feedback on the owned digest and suppresses the same canonical paper from subsequent digests

#### Scenario: User selects read later
- **WHEN** the user selects `later`
- **THEN** the inbox records the feedback and adds the paper to the user's library reading queue through the existing personal-ingestion workflow

### Requirement: Historical digest cards remain compatible
The digest inbox SHALL continue rendering older recommendation metadata that does not contain ranking, provider, timestamp, or ingestion-token fields.

#### Scenario: User opens older digest
- **WHEN** a historical digest contains only title and arXiv identifier
- **THEN** the user can still view the card and use the arXiv fallback actions

