## MODIFIED Requirements

### Requirement: Chat composer aligns with the usable viewport bottom
The chat workspace SHALL fill the available viewport below the application header and outer page margins so that no unused layout area appears below the composer, and SHALL keep composer padding compact enough that the conversation area remains visibly large.

#### Scenario: Desktop chat layout
- **WHEN** a user opens the chat page on a desktop-width viewport
- **THEN** the chat composer is aligned with the usable bottom edge after accounting for the header and desktop page margins
- **AND** the composer area does not create a large blank band below or around the input panel.

#### Scenario: Mobile chat layout
- **WHEN** a user opens the chat page on a mobile-width viewport
- **THEN** the chat composer is aligned with the usable bottom edge after accounting for the header and mobile page margins
- **AND** vertical padding is compact enough to preserve message reading space.
