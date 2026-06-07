# api-error-feedback Specification

## Purpose
TBD - created by archiving change unify-primary-workflow-error-recovery. Update Purpose after archive.
## Requirements
### Requirement: Shared API Error Alert
The frontend SHALL provide a reusable alert component that renders structured API error details with message, recovery guidance, category, retryability, and status metadata.

#### Scenario: Page renders structured failure
- **WHEN** a page passes structured API error details to the shared alert
- **THEN** the alert displays the failure title, parsed message, recovery guidance, category, retryability label, and HTTP status when present
- **AND** the alert can be dismissed without clearing unrelated page data.

### Requirement: Primary Workflow Pages Show Persistent Recovery Guidance
The primary workflow pages SHALL display persistent structured recovery guidance for important API failures instead of relying only on short-lived toast messages.

#### Scenario: Primary workflow API action fails
- **WHEN** a paper, research, research project, or writing API operation fails
- **THEN** the page stores the latest structured failure and renders it through the shared API error alert
- **AND** successful operations clear stale failure guidance where appropriate.

