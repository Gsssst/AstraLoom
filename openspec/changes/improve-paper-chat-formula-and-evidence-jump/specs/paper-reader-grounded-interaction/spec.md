## ADDED Requirements

### Requirement: Paper chat evidence markers navigate to PDF evidence pages
The paper detail chat SHALL render answer evidence markers as interactive controls when the marker maps to a current-paper evidence reference. Clicking a page-backed evidence marker SHALL navigate the PDF reader to the referenced page and expose the matching evidence context.

#### Scenario: User clicks an answer evidence marker
- **WHEN** an assistant answer contains `[E1]`
- **AND** the assistant message includes a paper evidence reference with id `E1` and a PDF page number
- **THEN** `[E1]` is rendered as an interactive evidence marker
- **AND** clicking it navigates the PDF reader to that page
- **AND** the paper evidence context becomes visible for inspection.

#### Scenario: Evidence marker has no PDF page
- **WHEN** an assistant answer contains `[E2]`
- **AND** the matching evidence reference has no page number
- **THEN** the marker remains visually identifiable
- **AND** clicking it does not change the PDF page.

### Requirement: Display formula tags remain separated from formulas
Markdown-rendered display formulas in paper chat SHALL keep KaTeX equation tags visually separated from the formula body while preserving horizontal scrolling for long equations.

#### Scenario: Long formula with equation number
- **WHEN** an assistant answer contains a display equation with a KaTeX equation tag
- **THEN** the equation number remains at the right side of the display equation
- **AND** the equation body does not overlap the number.
