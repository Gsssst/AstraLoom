## ADDED Requirements

### Requirement: Action Center Shows Recovery Guidance

The Action Center frontend SHALL display structured recovery guidance when action loading or execution fails.

#### Scenario: Action list fails to load
- **WHEN** Action Center cannot load workflow actions
- **THEN** it displays a persistent failure message with recovery guidance and retryability metadata.

#### Scenario: Executable action fails
- **WHEN** an API-backed action fails
- **THEN** the page preserves the action title and displays structured recovery guidance from the shared API error helper.
