# Capability: Cross Module Action Center

## ADDED Requirements

### Requirement: Action center can expose executable maintenance actions

The workflow action API SHALL identify when an action can be executed directly instead of only navigating to another module.

#### Scenario: Knowledge-base maintenance is needed

- **GIVEN** a user has saved papers that are missing full text or embeddings
- **WHEN** the action center builds paper workflow actions
- **THEN** the relevant action includes an API endpoint, HTTP method, action label, and admin requirement marker
- **AND** the action still includes a path to the detailed maintenance page

### Requirement: Users can run bounded maintenance actions from the action center

The frontend SHALL execute API actions from the action center and keep users informed of the result.

#### Scenario: User runs a maintenance action

- **GIVEN** the action center displays an executable knowledge-base maintenance action
- **WHEN** the user clicks its primary action button
- **THEN** the frontend calls the action endpoint
- **AND** displays a success or error message
- **AND** refreshes the action list after completion

#### Scenario: User wants detailed controls

- **GIVEN** an executable action also has a module path
- **WHEN** the user chooses to inspect details
- **THEN** the frontend navigates to the referenced module page
