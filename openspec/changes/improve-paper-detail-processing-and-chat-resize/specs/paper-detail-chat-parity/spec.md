## ADDED Requirements

### Requirement: Paper detail chat panel is resizable without PDF
The paper detail page SHALL allow desktop users to resize the AI Q&A panel horizontally when the PDF viewer is hidden.

#### Scenario: User resizes content and chat layout
- **WHEN** a desktop user views a paper detail page with the PDF panel hidden
- **THEN** a visible resize handle SHALL allow adjusting the content panel and AI Q&A panel widths within bounded limits

#### Scenario: Mobile layout remains tabbed
- **WHEN** a user views the paper detail page on a mobile viewport
- **THEN** the page SHALL keep the existing tabbed content/PDF/chat layout without a desktop resize handle
