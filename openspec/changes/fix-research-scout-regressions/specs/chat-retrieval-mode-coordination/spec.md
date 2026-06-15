## MODIFIED Requirements

### Requirement: Paper discovery prompts route to scholarly scout mode
The chat system SHALL route explicit paper-finding prompts to Research Scout behavior even when the visible assistant mode was not manually switched.

#### Scenario: User asks to find papers in ordinary mode
- **WHEN** a user asks to find, list, recommend, or search for papers
- **AND** the prompt includes scholarly constraints such as topic, year, venue, institution, or paper count
- **THEN** the request is handled as Research Scout
- **AND** the streamed metadata includes `research_scout.enabled = true`
- **AND** the response includes structured candidate metadata when scholarly discovery returns papers.

#### Scenario: Research Scout does not use generic web fallback references
- **WHEN** a request is handled as Research Scout
- **THEN** ordinary web search context is not injected into the model context
- **AND** returned references are scholarly scout candidates, local/upload evidence, or empty
- **AND** unrelated generic web pages are not displayed as scout sources.
