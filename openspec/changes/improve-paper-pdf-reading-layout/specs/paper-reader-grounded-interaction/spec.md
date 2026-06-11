## ADDED Requirements

### Requirement: Enhanced PDF reader supports continuous scrolling
The paper PDF reader SHALL render loaded PDF pages in a continuous vertical scroll flow and SHALL allow users to move between pages by scrolling.

#### Scenario: User scrolls through PDF pages
- **WHEN** a PDF document loads in the enhanced reader
- **THEN** all available pages are shown in vertical order within the PDF scroll area
- **AND** the user can reach the next page by scrolling down instead of clicking a next-page button

#### Scenario: Current page follows scroll position
- **WHEN** the user scrolls the PDF reader
- **THEN** the displayed current page number updates to the page closest to the reading position

#### Scenario: Target page navigation
- **WHEN** the application requests a target PDF page
- **THEN** the PDF reader scrolls that page into view

### Requirement: Continuous PDF text selection remains page-aware
The paper reader SHALL preserve selectable PDF text and report the selected page number while multiple PDF pages are visible.

#### Scenario: User selects text on a rendered PDF page
- **WHEN** the user selects eligible text in a continuous PDF page
- **THEN** the paper question composer can receive the selected text with that page's page number

### Requirement: Paper PDF and AI Q&A panels are resizable
The paper detail desktop layout SHALL allow users to adjust the relative widths of the PDF and AI Q&A panels with a pointer drag.

#### Scenario: User drags the panel splitter
- **WHEN** the desktop paper detail view shows both PDF and AI Q&A panels
- **AND** the user drags the splitter between the panels
- **THEN** the PDF panel width changes within bounded minimum and maximum limits
- **AND** the AI Q&A panel uses the remaining width

#### Scenario: User collapses AI Q&A by dragging right
- **WHEN** the user drags the splitter beyond the collapse threshold toward the right edge
- **THEN** the AI Q&A panel collapses into a compact rail
- **AND** a visible control allows reopening the AI Q&A panel

#### Scenario: Mobile layout remains tabbed
- **WHEN** the paper detail page is displayed on a mobile viewport
- **THEN** the PDF, content, and AI Q&A panels continue to use the existing tab-style panel switching
