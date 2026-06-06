## ADDED Requirements

### Requirement: Admins can test the active LLM connection
The system SHALL provide an admin-only settings action to test the currently active LLM provider/model.

#### Scenario: Active model test succeeds
- **WHEN** an admin triggers the LLM connection test
- **THEN** the backend sends a minimal prompt to the active model
- **AND** returns provider, model, success state, elapsed milliseconds, and a short response preview
- **AND** the response does not include API keys or API base URLs

#### Scenario: Active model is not configured
- **WHEN** the active provider is missing required server-side configuration
- **THEN** the test returns a clear client-visible error
- **AND** no API key value is exposed

#### Scenario: Non-admin attempts the test
- **WHEN** a non-admin user triggers the test endpoint
- **THEN** the request is rejected by the existing admin authorization boundary

### Requirement: Settings UI displays LLM test feedback
The Settings API tab SHALL expose a connection test control for the selected model.

#### Scenario: Test finishes successfully
- **WHEN** the admin clicks the test control and the backend succeeds
- **THEN** the UI shows the tested model, elapsed time, and response preview

#### Scenario: Test fails
- **WHEN** the backend returns an error
- **THEN** the UI displays the existing API error feedback without changing the selected model
