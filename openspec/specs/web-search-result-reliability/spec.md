# web-search-result-reliability Specification

## Purpose
TBD - created by archiving change web-search-result-reliability. Update Purpose after archive.
## Requirements
### Requirement: Web search uses provider fallback
The chat web-search service SHALL try a secondary provider when the primary provider does not return usable parsed results.

#### Scenario: Primary provider returns results
- **WHEN** Bing returns parsable result items
- **THEN** the service returns bounded Bing snippets without requesting the fallback provider

#### Scenario: Primary provider returns no usable results
- **WHEN** Bing returns no parsable result items
- **THEN** the service requests DuckDuckGo HTML results and returns bounded parsed snippets when available

### Requirement: Web search degradation is transparent
The chat assistant SHALL receive explicit context when web enhancement was requested but no usable online source was retrieved.

#### Scenario: All external providers fail
- **WHEN** web enhancement is enabled and every external provider returns no usable results
- **THEN** the model context states that the current request did not obtain valid online sources

