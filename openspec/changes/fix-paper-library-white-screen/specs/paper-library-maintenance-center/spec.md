## MODIFIED Requirements

### Requirement: Maintenance Actions
The paper library SHALL render maintenance controls and long-running job status without runtime initialization errors.

#### Scenario: Paper library renders with visual evidence job helpers
- **WHEN** the paper library page initializes
- **THEN** maintenance job polling helpers are already initialized before they are referenced by React hooks
- **AND** the page does not blank due to a callback initialization error.
