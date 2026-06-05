# scholarly-source-pdf-and-google-scholar Specification

## Purpose
TBD - created by archiving change scholarly-source-pdf-and-google-scholar. Update Purpose after archive.
## Requirements
### Requirement: Resilient arXiv retrieval
The system SHALL space arXiv API requests and SHALL try a configured alternate arXiv API endpoint when the primary endpoint is throttled, times out, or otherwise fails.

#### Scenario: Primary arXiv endpoint fails
- **WHEN** the primary arXiv API endpoint raises an HTTP or transport error
- **THEN** the service tries the configured fallback endpoint before degrading to another scholarly provider

### Requirement: OpenAlex open PDF preservation
The system SHALL preserve an OpenAlex open-access PDF URL when OpenAlex supplies one and SHALL expose it to paper discovery consumers.

#### Scenario: OpenAlex result has a best open-access location
- **WHEN** an OpenAlex work includes `best_oa_location.pdf_url`
- **THEN** the normalized result and any newly ingested paper preserve that PDF URL

#### Scenario: OpenAlex result has no open-access PDF
- **WHEN** an OpenAlex work does not include an open PDF URL
- **THEN** the interface does not present a PDF action for that work

### Requirement: Explicit comprehensive scholarly discovery
The system SHALL provide a comprehensive scholarly-search mode that aggregates supported remote providers, deduplicates equivalent works, and retains the visible source of each result.

#### Scenario: Comprehensive discovery returns multiple providers
- **WHEN** a user searches with the comprehensive remote source mode
- **THEN** the system queries supported providers concurrently and returns deduplicated results with provider labels

### Requirement: Optional Google Scholar provider
The system SHALL integrate Google Scholar results only through the configured SerpApi Google Scholar engine and SHALL NOT scrape Google Scholar HTML directly.

#### Scenario: SerpApi key is configured
- **WHEN** the user runs a Google Scholar or comprehensive search and `SERPAPI_API_KEY` is configured
- **THEN** the system includes normalized SerpApi Google Scholar results

#### Scenario: SerpApi key is absent
- **WHEN** the user runs a comprehensive search without `SERPAPI_API_KEY`
- **THEN** the system continues with the other scholarly providers without failing

### Requirement: Open PDF discovery actions
The paper-library interface SHALL display an open-PDF action only for results that expose a PDF URL and SHALL offer individual and comprehensive scholarly provider selectors.

#### Scenario: Remote preview exposes an open PDF
- **WHEN** a remote search result contains a PDF URL
- **THEN** the result card and abstract dialog provide an open-PDF action

