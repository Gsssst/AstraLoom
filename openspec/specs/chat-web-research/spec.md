# chat-web-research Specification

## Purpose
TBD - created by archiving change chat-web-research-and-typescript-cleanup. Update Purpose after archive.
## Requirements
### Requirement: Bounded multi-query web research
When web enhancement is enabled, the system SHALL derive a bounded set of search queries according to the selected search depth and SHALL aggregate results from supported web providers.

#### Scenario: Quick mode limits breadth
- **WHEN** a user enables web enhancement with quick search depth
- **THEN** the system searches only the original user query

#### Scenario: Deep mode expands breadth
- **WHEN** a user enables web enhancement with deep search depth
- **THEN** the system searches the original query and additional bounded query variants

### Requirement: Concurrent multi-provider retrieval
The system SHALL query supported web search providers concurrently and SHALL continue processing successful provider results if another provider fails.

#### Scenario: One provider fails
- **WHEN** one web search provider raises an error and another returns results
- **THEN** the system returns the successful provider results without failing the chat request

### Requirement: Structured web evidence
The system SHALL normalize, deduplicate, and rank web search results before injecting a bounded evidence context into the model prompt.

#### Scenario: Duplicate URL returned by multiple providers
- **WHEN** multiple providers return results that resolve to the same canonical URL
- **THEN** the system injects that URL only once

### Requirement: Clickable web citations
The system SHALL return web references alongside local paper references for both normal chat and paper Q&A so users can inspect the sources used for grounding.

#### Scenario: Chat receives web evidence
- **WHEN** web retrieval returns at least one source
- **THEN** the assistant message metadata includes clickable web reference URLs

### Requirement: Honest degraded operation
The system SHALL clearly tell the model when web enhancement produced no usable sources and SHALL avoid claiming that network retrieval succeeded.

#### Scenario: No provider returns results
- **WHEN** all enabled web providers fail or return no usable results
- **THEN** the system inserts a degraded-operation instruction and continues with any available local context

