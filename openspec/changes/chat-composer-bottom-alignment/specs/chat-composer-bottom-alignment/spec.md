## ADDED Requirements

### Requirement: Chat composer aligns with the usable viewport bottom
The chat workspace SHALL fill the available viewport below the application header and outer page margins so that no unused layout area appears below the composer.

#### Scenario: Desktop chat layout
- **WHEN** a user opens the chat page on a desktop-width viewport
- **THEN** the chat composer is aligned with the usable bottom edge after accounting for the header and desktop page margins

#### Scenario: Mobile chat layout
- **WHEN** a user opens the chat page on a mobile-width viewport
- **THEN** the chat composer is aligned with the usable bottom edge after accounting for the header and mobile page margins
