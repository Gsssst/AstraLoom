## ADDED Requirements

### Requirement: PDF evidence locator requests are one-shot
The PDF reader SHALL execute each evidence locator request id at most once. After a locator request scrolls to a cited page and attempts snippet localization, later component re-renders SHALL NOT replay the same locator or force the user back to the localized passage while they manually scroll.

#### Scenario: User scrolls away after evidence localization
- **WHEN** a user clicks an evidence marker and the PDF reader localizes request id `7`
- **AND** the user scrolls to another page
- **THEN** the PDF reader does not replay request id `7`
- **AND** the reader does not scroll back to the old evidence position.

#### Scenario: User clicks another evidence marker
- **WHEN** a user clicks a later evidence marker with request id `8`
- **THEN** the PDF reader executes the new locator request
- **AND** navigates to the new cited page.

### Requirement: Page-only PDF target jumps are one-shot
The PDF reader SHALL execute a page-only target jump only when the target page value changes. Later re-renders with the same target page SHALL NOT override manual scrolling.

#### Scenario: User scrolls after a page jump
- **WHEN** a page-only target jump navigates to page `4`
- **AND** the user scrolls to page `5`
- **THEN** re-renders with target page `4` do not scroll the reader back to page `4`.
