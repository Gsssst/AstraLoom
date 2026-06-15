## MODIFIED Requirements

### Requirement: Chat composer aligns with the usable viewport bottom
The chat workspace SHALL fill the available viewport below the application header and outer page margins so that no unused layout area appears below the composer. The bottom composer SHALL remain visually grounded to the workspace edge while using restrained workbench styling.

#### Scenario: Desktop chat layout
- **WHEN** a user opens the chat page on a desktop-width viewport
- **THEN** the chat composer is aligned with the usable bottom edge after accounting for the header and desktop page margins
- **AND** the composer does not appear as an oversized floating marketing card

#### Scenario: Mobile chat layout
- **WHEN** a user opens the chat page on a mobile-width viewport
- **THEN** the chat composer is aligned with the usable bottom edge after accounting for the header and mobile page margins
- **AND** the composer controls remain usable without overlap
