## ADDED Requirements

### Requirement: Configured structured providers are preferred

The system SHALL query configured structured web-search providers before HTML fallback providers.

#### Scenario: Tavily is configured

- **WHEN** a Tavily API key is configured
- **THEN** web research queries Tavily
- **AND** structured Tavily results are normalized into the shared web result contract

### Requirement: Zero-configuration fallback remains available

The system SHALL preserve Bing and DuckDuckGo HTML search as fallback providers.

#### Scenario: No structured provider is configured

- **WHEN** a user enables web research without any structured provider configuration
- **THEN** the system queries Bing and DuckDuckGo HTML providers
- **AND** returns available normalized results

#### Scenario: Structured results are insufficient

- **WHEN** configured structured providers fail or return fewer unique results than requested
- **THEN** the system queries HTML fallback providers
- **AND** merges unique fallback results until the requested result bound is reached

### Requirement: Provider configuration is observable without leaking secrets

The system SHALL report active web-search provider names without returning API keys.

#### Scenario: Settings API is requested

- **WHEN** an authenticated user requests API configuration
- **THEN** the response contains available web-search provider names
- **AND** the response does not contain any web-search API key value

### Requirement: Provider failures are isolated

The system SHALL continue web research when an individual provider fails.

#### Scenario: One structured provider fails

- **WHEN** one configured structured provider raises an error
- **THEN** results from remaining configured providers and fallback providers remain eligible for return
