## ADDED Requirements

### Requirement: Shared Workflow State Components
The frontend SHALL provide reusable workflow state components for primary page loading, unavailable, empty, and long-running progress feedback using the existing Ant Design component stack.

#### Scenario: Shared loading state preserves page context
- **WHEN** a primary workflow page is loading required data
- **THEN** the page renders a shared loading state within the normal PageShell content instead of replacing the whole page with a standalone spinner

#### Scenario: Shared unavailable state explains the condition
- **WHEN** required primary workflow data cannot be displayed or is not found
- **THEN** the page renders a shared unavailable state with a clear title, description, and optional recovery action

### Requirement: Primary Workflow Empty States Are Actionable
Primary workflow pages SHALL render actionable empty states that explain what is missing and offer the next relevant action when a list, workspace, or selected resource is empty.

#### Scenario: Empty workflow list
- **WHEN** a primary workflow list has no items after loading completes
- **THEN** the empty state explains what to create or search next
- **AND** it can include an action that starts the relevant workflow

#### Scenario: Empty filtered result
- **WHEN** a primary workflow list has no results because of a filter or query
- **THEN** the empty state distinguishes that from a truly empty workspace and offers a way to clear or broaden the filter

### Requirement: Long-Running Workflow Progress Is Visible
Primary workflow pages SHALL show visible progress feedback for long-running generation, maintenance, export, or pipeline operations when progress, phase, or status text is available in the frontend.

#### Scenario: Operation exposes progress metadata
- **WHEN** a long-running workflow operation has a percent, phase, or status message
- **THEN** the page displays that metadata through a consistent progress feedback component

#### Scenario: Operation is running without exact percent
- **WHEN** a long-running workflow operation is running but only a status label is known
- **THEN** the page displays an indeterminate progress state without inventing a precise percentage
