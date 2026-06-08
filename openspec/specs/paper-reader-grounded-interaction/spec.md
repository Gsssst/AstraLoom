# paper-reader-grounded-interaction Specification

## Purpose
TBD - created by archiving change paper-reader-grounded-interaction. Update Purpose after archive.
## Requirements
### Requirement: Paper reading workspace remains viewport-bound
The paper detail workspace SHALL keep PDF reading and paper chat panels within the available viewport height. AI answer growth SHALL scroll inside the chat message list without expanding the page or shrinking the visible PDF area.

#### Scenario: Long paper chat answer
- **WHEN** a paper AI conversation accumulates enough content to exceed the visible chat area
- **THEN** the chat message list scrolls internally while the composer and PDF panel remain visible

### Requirement: Named paper sections receive targeted retrieval
The paper AI backend SHALL recognize common paper section requests in English and Chinese and SHALL retrieve from a matching detected section before applying chunk ranking. The backend SHALL fall back to document-wide retrieval when the named section cannot be found.

#### Scenario: User asks to explain the introduction
- **WHEN** a paper contains an `Introduction` heading and the user asks to explain the paper introduction
- **THEN** the AI context includes introduction text before unrelated later sections

#### Scenario: Requested section is unavailable
- **WHEN** the user asks about a section that cannot be detected in the extracted paper text
- **THEN** the backend uses document-wide retrieval so the question can still be answered

### Requirement: Selected PDF text enters the paper question composer
The PDF reader SHALL expose selectable text and SHALL show selected text with its PDF page number as a removable quote card above the paper AI question editor. The quote SHALL be included in the model question context without replacing or polluting the user's editable draft.

#### Scenario: User selects a passage in the PDF
- **WHEN** the user selects a passage of PDF text longer than five characters
- **THEN** the paper question composer shows a removable quote card with the selected text and source page number

#### Scenario: User already drafted a question
- **WHEN** the user selects PDF text while the composer already contains text
- **THEN** the selected quote card is added without modifying or discarding the existing draft

### Requirement: Paper question editor supports multiline drafting
The paper AI question editor SHALL grow automatically as the user enters multiple lines up to a bounded maximum height. Content beyond that height SHALL scroll inside the editor.

#### Scenario: User writes a multiline paper question
- **WHEN** the user enters line breaks in a paper AI question
- **THEN** the editor expands to show multiple lines while preserving the visible chat area

### Requirement: Paper full text loading uses available PDF parsers
The paper AI backend SHALL extract and persist paper full text with an installed PDF parser before answering section-specific questions. Concurrent requests for the same missing full text SHALL share one loading task, and timed-out foreground waits SHALL allow that task to finish in the background.

#### Scenario: Paper detail preload and question overlap
- **WHEN** paper detail preload and a paper question request full text for the same paper at the same time
- **THEN** the backend performs one shared PDF loading task and persists the extracted text

#### Scenario: Primary PDF parser is available
- **WHEN** a downloaded PDF contains extractable text and `pdfplumber` is installed
- **THEN** the backend extracts full text without requiring optional `fitz`

### Requirement: Paper thinking mode exits stalled reasoning
The paper AI backend SHALL limit the primary thinking stream duration and SHALL switch to a stable answer stream when the model emits reasoning without visible answer content past that limit.

#### Scenario: Thinking stream does not reach an answer
- **WHEN** the primary paper answer stream exceeds its reasoning time limit without visible content
- **THEN** the backend emits a recovery status and begins a stable answer stream

### Requirement: PDF text selection remains readable
The paper reader SHALL style PDF text selection so selected passages remain readable and adjacent lines do not visually merge into one heavy block.

#### Scenario: User selects multiple PDF lines
- **WHEN** the user highlights text across multiple lines in the PDF reader
- **THEN** the selection uses a lighter translucent overlay
- **AND** line boxes retain enough visual separation to distinguish adjacent selected lines

#### Scenario: Selected text is captured for paper chat
- **WHEN** the user selects PDF text for a quote card
- **THEN** the visual selection styling does not prevent the selected text from being captured for the paper question composer

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
