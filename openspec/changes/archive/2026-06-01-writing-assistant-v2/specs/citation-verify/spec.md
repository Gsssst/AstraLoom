## ADDED Requirements

### Requirement: Cross-verify citations against external sources

The system SHALL extract all citation references from AI-generated text (marked as [1], [2], etc. or by paper title), then verify each citation against Semantic Scholar API, CrossRef API, and arXiv API in parallel. A citation SHALL be marked "verified" when at least 2 out of 3 sources confirm the paper exists with matching title and author.

#### Scenario: Citation verified by all three sources

- **WHEN** AI-generated text cites "Attention Is All You Need" (Vaswani et al., 2017)
- **AND** Semantic Scholar, CrossRef, and arXiv all return matching results
- **THEN** the citation SHALL be marked as "verified" with confidence "high"
- **AND** SHALL include the DOI from CrossRef as authoritative identifier

#### Scenario: Citation verified by two of three sources

- **WHEN** arXiv and Semantic Scholar match but CrossRef returns no result
- **THEN** the citation SHALL be marked as "verified" with confidence "medium"
- **AND** SHALL note which source did not confirm

#### Scenario: Citation not found in any source

- **WHEN** AI-generated text cites a paper title that returns no results from any API
- **THEN** the citation SHALL be marked as "likely_hallucination"
- **AND** the frontend SHALL display a warning icon next to the citation

### Requirement: Graceful degradation when external APIs unavailable

The system SHALL handle external API failures gracefully. When one or more APIs are unavailable (timeout, rate limit, error), the verification SHALL proceed with available sources. If all external APIs fail, the system SHALL fall back to local knowledge base verification.

#### Scenario: One API times out

- **WHEN** Semantic Scholar API times out after 10 seconds
- **AND** CrossRef and arXiv respond successfully
- **THEN** verification SHALL complete using CrossRef and arXiv results
- **AND** the response SHALL note that Semantic Scholar was unavailable

#### Scenario: All external APIs fail

- **WHEN** all three external APIs return errors
- **THEN** the system SHALL check the local knowledge base for matching papers
- **AND** mark citations as "unverified" if local check also fails
- **AND** SHALL NOT block the writing workflow

### Requirement: Verification results caching

The system SHALL cache citation verification results with a 24-hour TTL. Within the TTL window, repeated verification requests for the same paper title SHALL return cached results without calling external APIs.

#### Scenario: Cache hit for recently verified citation

- **WHEN** a citation was verified within the last 24 hours
- **AND** the same paper is cited again
- **THEN** the system SHALL return cached verification result
- **AND** SHALL NOT make external API calls

### Requirement: Auto-fix suggestion for incorrect citations

When a citation is marked as "likely_hallucination", the system SHALL attempt to find the closest real paper by searching with the hallucinated title as query. If a close match is found (title similarity > 0.7), the system SHALL suggest it as a replacement.

#### Scenario: Suggest replacement for hallucinated citation

- **WHEN** a citation "Deep Learning for Everything" is marked as hallucination
- **AND** search finds "Deep Learning: A Comprehensive Survey" with title similarity 0.75
- **THEN** the system SHALL suggest the real paper as a replacement
- **AND** SHALL flag it as "suggested_replacement" not "verified"
