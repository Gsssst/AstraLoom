## ADDED Requirements

### Requirement: Responsive application navigation
The application SHALL provide desktop sidebar navigation on wide screens and a drawer-based navigation experience on narrow screens.

#### Scenario: Open navigation on a narrow screen
- **WHEN** a user views an internal page below the medium breakpoint and activates the navigation control
- **THEN** the application displays the available internal routes in an overlay drawer without permanently reducing content width

#### Scenario: Navigate from the mobile drawer
- **WHEN** a user selects an internal route from the mobile navigation drawer
- **THEN** the application navigates to that route and closes the drawer

### Requirement: Responsive paper library controls
The paper library SHALL keep search, filters, and available actions usable without horizontal page overflow on narrow screens.

#### Scenario: Search papers on a narrow screen
- **WHEN** a user views the paper library below the medium breakpoint
- **THEN** the filters and search field reflow to available width while paper cards remain readable

### Requirement: Responsive paper reading workspace
The paper detail page SHALL provide full-width mobile modes for paper content, PDF reading, and AI Q&A while retaining the desktop split workspace.

#### Scenario: Switch paper detail modes on a narrow screen
- **WHEN** a user activates the content, PDF, or Q&A mode on a narrow paper detail page
- **THEN** the selected panel fills the available workspace and the other panels are hidden

#### Scenario: Read a paper on a wide screen
- **WHEN** a user views a paper detail page at or above the medium breakpoint
- **THEN** the application preserves the existing split reader and AI Q&A workspace behavior

### Requirement: Responsive authentication cards
The login and registration pages SHALL keep their cards within the viewport with comfortable edge spacing on narrow screens.

#### Scenario: Open authentication on a phone-sized viewport
- **WHEN** a user opens login or registration below the medium breakpoint
- **THEN** the card width adapts to the viewport and does not create horizontal overflow

### Requirement: Responsive chat workspace
The chat workspace SHALL provide a narrow-screen session drawer and allow toolbar actions to wrap without blocking message reading or composition.

#### Scenario: Open chat sessions on a narrow screen
- **WHEN** a user activates the chat session control below the medium breakpoint
- **THEN** the session list appears in an overlay drawer and the message workspace retains full width

#### Scenario: Use chat tools on a narrow screen
- **WHEN** the chat workspace is displayed below the medium breakpoint
- **THEN** the toolbar reflows within the viewport and the composer remains usable
