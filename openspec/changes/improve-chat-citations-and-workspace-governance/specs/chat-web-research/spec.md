## MODIFIED Requirements

### Requirement: Structured web evidence
The system SHALL normalize, deduplicate, rank, and query-filter web search results before injecting a bounded evidence context into the model prompt.

#### Scenario: Duplicate URL returned by multiple providers
- **WHEN** multiple providers return results that resolve to the same canonical URL
- **THEN** the system injects that URL only once

#### Scenario: Fallback search returns off-topic results
- **GIVEN** a user asks about an English technical research topic
- **AND** a fallback web provider returns Chinese dictionary pages for an unrelated single-character token
- **WHEN** web search references are prepared
- **THEN** those off-topic pages are excluded from the prompt context and assistant references

### Requirement: Clickable web citations
The system SHALL return web references alongside local paper references for both normal chat and paper Q&A so users can inspect the retrieved sources used for grounding.

#### Scenario: Chat receives web evidence
- **WHEN** web retrieval returns at least one query-relevant source
- **THEN** the assistant message metadata includes clickable web reference URLs
- **AND** each web reference includes provider and query metadata for auditability
