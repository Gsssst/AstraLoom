## ADDED Requirements

### Requirement: Paper chat answer evidence drawer
The paper-detail AI Q&A panel SHALL provide a categorized evidence drawer for assistant answers that include references or evidence metadata.

#### Scenario: User opens evidence drawer from an answer
- **WHEN** an assistant answer contains references
- **THEN** the answer shows a compact action for opening the detailed evidence drawer

#### Scenario: Evidence is grouped by type
- **WHEN** the evidence drawer opens
- **THEN** references are grouped into current-paper text, tables, visual/OCR evidence, web sources, and related-paper sources when those groups are present

#### Scenario: User clicks current-paper evidence
- **WHEN** a user clicks current-paper evidence in the drawer and the reference has a page
- **THEN** the paper detail view jumps to that PDF page using the existing evidence navigation behavior

#### Scenario: User clicks web evidence
- **WHEN** a user clicks a web evidence item in the drawer
- **THEN** the source URL opens in a new browser tab using the existing external-source behavior

#### Scenario: Answer has evidence quality metadata
- **WHEN** an assistant answer includes evidence quality metadata
- **THEN** the evidence drawer shows the same confidence/coverage state as the compact answer summary
