## ADDED Requirements

### Requirement: Paper Library Shows Persistent API Recovery
The paper library frontend SHALL show persistent structured recovery guidance for failed paper search, import, collection, reading status, maintenance, deletion, report, and export operations.

#### Scenario: Paper library action fails
- **WHEN** a paper library API action fails
- **THEN** the paper library displays a structured recovery alert derived from the shared API error helper
- **AND** the user can dismiss the alert and keep current page state.

#### Scenario: Paper library action succeeds after a previous failure
- **WHEN** a paper library API action succeeds after an earlier failure
- **THEN** stale paper-library recovery guidance is cleared when the successful action makes it obsolete.
