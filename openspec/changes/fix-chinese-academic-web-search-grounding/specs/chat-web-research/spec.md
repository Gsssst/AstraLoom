## MODIFIED Requirements

### Requirement: Bounded multi-query web research
When web enhancement is enabled, the system SHALL derive a bounded set of topic-focused search queries according to the selected search depth and SHALL aggregate results from supported web providers.

#### Scenario: Quick mode limits breadth
- **WHEN** a user enables web enhancement with quick search depth
- **THEN** the system searches only one topic-focused query

#### Scenario: Deep mode expands breadth
- **WHEN** a user enables web enhancement with deep search depth
- **THEN** the system searches the topic-focused query and additional bounded query variants

#### Scenario: Chinese academic paper request is normalized
- **WHEN** a user asks in Chinese to find papers about a research topic
- **THEN** the system removes polite request scaffolding, requested counts, and generic academic filler from planned search queries
- **AND** the planned queries retain the research topic and may include deterministic English aliases for that topic

### Requirement: Structured web evidence
The system SHALL normalize, deduplicate, rank, and topic-filter web search results before injecting a bounded evidence context into the model prompt.

#### Scenario: Duplicate URL returned by multiple providers
- **WHEN** multiple providers return results that resolve to the same canonical URL
- **THEN** the system injects that URL only once

#### Scenario: Fallback search returns off-topic Chinese language pages
- **GIVEN** a user asks for papers about a Chinese academic research topic
- **AND** a fallback web provider returns dictionary or translation pages for request scaffolding words
- **WHEN** web search references are prepared
- **THEN** those off-topic pages are excluded from the prompt context and assistant references

### Requirement: Clickable web citations
The system SHALL return web references alongside local paper references for both normal chat and paper Q&A so users can inspect the retrieved sources used for grounding.

#### Scenario: Chat receives web evidence
- **WHEN** web retrieval returns at least one topic-relevant source
- **THEN** the assistant message metadata includes clickable web reference URLs
- **AND** each web reference includes provider and retrieval query metadata for auditability
