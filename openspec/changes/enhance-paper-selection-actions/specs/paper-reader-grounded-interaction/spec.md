## ADDED Requirements

### Requirement: Paper text selection exposes contextual actions
The paper reader SHALL show a compact contextual action menu when users select eligible text in the paper detail view or PDF reader. The menu SHALL let users route the selected text to AI chat, explanation, copying, notes, and PDF annotations without immediately changing the question composer unless the user chooses an action.

#### Scenario: User selects text in the PDF
- **WHEN** a user selects more than five characters in the PDF reader
- **THEN** the paper detail page shows a contextual action menu near the selection
- **AND** the question composer is not changed until the user chooses an action

#### Scenario: User asks about selected PDF text
- **WHEN** the user chooses the ask action for selected PDF text
- **THEN** the selected text appears as a removable quote card with the PDF page number
- **AND** any existing editable draft question remains intact

#### Scenario: User saves selected PDF text
- **WHEN** an authenticated user chooses the save annotation action for selected PDF text
- **THEN** the existing paper annotation workflow persists the selected text with its PDF page number

#### Scenario: User selects text outside the PDF
- **WHEN** a user selects eligible paper-detail text outside the PDF reader
- **THEN** the menu offers AI, copy, and note actions
- **AND** it does not offer page-based PDF annotation saving
