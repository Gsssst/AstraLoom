## ADDED Requirements

### Requirement: Workspace backlink cards remain readable in narrow panels
The frontend SHALL render workspace backlink cards so project-space names, role/status tags, and link actions remain readable when the component is placed in a narrow resource-page sidebar.

#### Scenario: Linked workspace has a long name
- **WHEN** a resource page shows a linked project space with a long name in a narrow sidebar
- **THEN** the workspace name is displayed horizontally with truncation or normal word wrapping
- **AND** the status tags and unlink action remain accessible without forcing one-character vertical title wrapping

#### Scenario: Available workspace list is shown in a narrow panel
- **WHEN** editable spaces are listed as available for linking
- **THEN** each space row keeps the name, role tag, and add action readable within the card width
