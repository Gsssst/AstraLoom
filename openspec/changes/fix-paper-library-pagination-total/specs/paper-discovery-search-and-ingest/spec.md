## ADDED Requirements

### Requirement: Paper library search shows paginated totals
The paper-library interface SHALL display the total number of matching search-backed paper results returned by the paper search API, rather than only the number of items loaded on the current page.

#### Scenario: Local library has more papers than one page
- **WHEN** `/api/papers/search` returns `total=42`, `page=1`, `page_size=30`, and 30 items for a local paper-library browse
- **THEN** the paper-library subtitle shows 42 matching papers
- **AND** it does not label the current 30 loaded items as the full library size

#### Scenario: Filtered search has no matches
- **WHEN** `/api/papers/search` returns `total=0` for the active query and filters
- **THEN** the paper-library subtitle falls back to the normal search/manage description
- **AND** the empty state remains visible

### Requirement: Paper library search supports page navigation
The paper-library interface SHALL allow users to navigate pages for views backed by `/api/papers/search`.

#### Scenario: User moves to the second local page
- **WHEN** the current local paper-library search has more matching results than one page
- **AND** the user selects page 2
- **THEN** the frontend requests `/api/papers/search` with `page=2`
- **AND** the result list updates with the second page of papers

#### Scenario: Search context changes
- **WHEN** the user changes source, sort, query, year, ownership, processing, reading, or importance filters
- **THEN** the paper-library interface resets search-backed pagination to page 1
