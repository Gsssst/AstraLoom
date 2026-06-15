## ADDED Requirements

### Requirement: Research Scout candidate cards are visible for paper discovery
Research Scout SHALL surface structured candidate cards and evaluation metadata for paper discovery responses.

#### Scenario: Scholarly discovery returns candidates
- **WHEN** Research Scout finds candidate papers
- **THEN** the assistant message metadata includes candidate cards
- **AND** each card includes import/classification/project actions
- **AND** each card includes evaluation dimensions or a heuristic fallback
- **AND** venue/year constraints are represented in intent and constraint match metadata.

#### Scenario: Scholarly discovery returns no candidates
- **WHEN** Research Scout finds no candidate papers after arXiv-first and broad scholarly fallback retrieval
- **THEN** the response explains that scholarly discovery returned no candidates
- **AND** it does not fall back to unrelated generic web pages as if they were paper evidence.

### Requirement: Research Scout prefers arXiv PDF candidates with scholarly fallback
Research Scout SHALL prefer arXiv PDF-backed candidates while using external scholarly providers as fallback and enrichment when arXiv-first retrieval is sparse.

#### Scenario: arXiv-first retrieval is sparse
- **WHEN** Research Scout's arXiv-enriched retrieval returns fewer candidates than the response target
- **THEN** it performs broad scholarly retrieval using the planned scholarly queries
- **AND** it can include Semantic Scholar, OpenAlex, or Google Scholar candidates when they are deduplicated and relevant.

#### Scenario: fallback candidates are returned
- **WHEN** a candidate did not originate from arXiv
- **THEN** its card preserves the actual provider and PDF availability
- **AND** the assistant does not claim an arXiv PDF exists unless the candidate metadata includes one.

### Requirement: Research Scout traces retrieval strategy
Research Scout SHALL expose the actual paper retrieval strategy through tool execution trace metadata.

#### Scenario: broad fallback runs
- **WHEN** broad scholarly fallback is used after arXiv-first retrieval
- **THEN** the search tool trace states that arXiv-first retrieval was broadened
- **AND** includes planned queries, provider labels, strategy name, fallback status, and candidate count.

#### Scenario: arXiv-first retrieval is sufficient
- **WHEN** arXiv-first retrieval produces enough deduplicated candidates
- **THEN** the search tool trace states that arXiv/PDF results were prioritized
- **AND** broad fallback is not reported as executed.
