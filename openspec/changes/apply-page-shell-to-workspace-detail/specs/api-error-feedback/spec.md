## ADDED Requirements

### Requirement: Workspace Detail Shows Recovery Guidance

The workspace detail frontend SHALL display structured recovery guidance when workspace loading or resource/member operations fail.

#### Scenario: Workspace load fails
- **WHEN** the workspace detail page cannot load the selected workspace
- **THEN** it displays a persistent failure message with recovery guidance before returning to the workspace list.

#### Scenario: Workspace operation fails
- **WHEN** loading candidates, adding/removing members, binding resources, or unlinking resources fails
- **THEN** the page displays structured recovery guidance from the shared API error helper.
