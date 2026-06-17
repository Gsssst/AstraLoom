## ADDED Requirements

### Requirement: Evidence links attempt page-internal PDF text localization
Paper-chat evidence links with both a PDF page number and snippet SHALL navigate to the cited page and SHALL attempt to locate the snippet within that page's rendered PDF text layer. When a match is found, the reader SHALL scroll the matched text into view and visually highlight it. When no match is found, the reader SHALL preserve the existing page-level navigation behavior.

#### Scenario: Evidence snippet is found on the cited page
- **WHEN** a user clicks a paper-chat evidence marker whose reference includes page `4` and a text snippet
- **THEN** the PDF reader navigates to page `4`
- **AND** searches page `4` text layer for the snippet
- **AND** scrolls the first matched text span into view
- **AND** applies a temporary evidence highlight.

#### Scenario: Evidence snippet is not matchable
- **WHEN** a user clicks a paper-chat evidence marker whose snippet cannot be found in the rendered page text layer
- **THEN** the PDF reader remains on the cited page
- **AND** the user receives non-blocking feedback that exact page-internal定位 was unavailable.

#### Scenario: Evidence has no snippet
- **WHEN** a user clicks a paper-chat evidence marker with a page number but no snippet
- **THEN** the PDF reader navigates to the cited page
- **AND** does not attempt page-internal text localization.
