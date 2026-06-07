## ADDED Requirements

### Requirement: Primary Workflow Pages Use Shared Shell
Primary workflow pages SHALL use the shared page shell for page identity, subtitle, page actions, width, and content spacing while preserving their workflow-specific controls inside the page body.

#### Scenario: Primary workflow page renders
- **WHEN** a user opens papers, research, research project detail, or writing
- **THEN** the page renders through the shared page shell
- **AND** top-level page actions render in the shell action area
- **AND** workflow filters, tabs, cards, and modals remain inside the body.

#### Scenario: Primary workflow page avoids bespoke hero wrapper
- **WHEN** a primary workflow page renders
- **THEN** it does not depend on a page-local gradient hero wrapper for the title and primary actions.
