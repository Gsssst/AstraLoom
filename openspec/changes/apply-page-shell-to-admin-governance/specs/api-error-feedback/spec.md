## ADDED Requirements

### Requirement: Admin Governance Shows Recovery Guidance

The Admin governance frontend SHALL display structured recovery guidance when admin data loading or user updates fail.

#### Scenario: Admin data loading fails
- **WHEN** admin overview, users, workspaces, or activity loading fails
- **THEN** the page displays a persistent failure message with recovery guidance and retryability metadata.

#### Scenario: Admin user update fails
- **WHEN** a user role or status update fails
- **THEN** the page displays structured recovery guidance from the shared API error helper.
