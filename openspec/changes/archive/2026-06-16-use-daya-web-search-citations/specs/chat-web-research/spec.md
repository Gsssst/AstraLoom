## MODIFIED Requirements

### Requirement: Clickable web citations
The system SHALL return web references alongside local paper references for normal chat so users can inspect the sources used for grounding.

#### Scenario: Compatible provider returns native citation annotations
- **GIVEN** web enhancement is enabled for ordinary chat
- **AND** the active LLM provider supports OpenAI-compatible native web search
- **WHEN** the model response includes `url_citation` annotations
- **THEN** the assistant message metadata includes clickable web reference URLs derived from those annotations
- **AND** those web references are marked as model annotation citations
- **AND** the system does not display unrelated pre-retrieved web candidates as citations for that turn

#### Scenario: Native provider web search has no usable annotations
- **GIVEN** web enhancement is enabled for ordinary chat
- **AND** the active LLM provider supports OpenAI-compatible native web search
- **WHEN** the provider call fails or returns no usable `url_citation` annotations
- **THEN** the system falls back to the existing local web retrieval path
- **AND** returned fallback web references remain labeled as retrieved evidence rather than model annotation citations

### Requirement: Structured web evidence
The system SHALL normalize, deduplicate, and label web references so users can distinguish provider-native model citations from local retrieval fallback evidence.

#### Scenario: Duplicate native citation URLs are returned
- **WHEN** a provider response contains duplicate `url_citation` annotations for the same URL
- **THEN** the assistant message metadata includes that URL only once

#### Scenario: Streaming response receives citations after content generation
- **WHEN** a streamed ordinary chat response uses provider-native web search
- **THEN** the frontend updates the streaming assistant message with the final annotation-derived references after the metadata event is received
