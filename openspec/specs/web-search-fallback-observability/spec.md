# web-search-fallback-observability Specification

## Purpose
TBD - created by archiving change web-search-fallback-observability. Update Purpose after archive.
## Requirements
### Requirement: Zero-configuration web search returns stable structured fallback results

The system SHALL use a structured no-key fallback when configured providers are unavailable.

#### Scenario: Bing HTML layout changes

- **WHEN** Bing HTML no longer matches legacy selectors
- **THEN** the system can still obtain normalized results from Bing RSS

### Requirement: Retrieval status is visible during generation

The system SHALL report the number of local-library and web sources used for a streamed answer.

#### Scenario: Web enhancement has results

- **WHEN** web enhancement returns usable sources
- **THEN** the stream status reports the web-source count

#### Scenario: Web enhancement returns no results

- **WHEN** web enhancement returns no usable sources
- **THEN** the stream status explicitly reports that web enhancement returned no usable sources

