## ADDED Requirements

### Requirement: Current-page formula order fallback handles missing labels
Paper Q&A evidence retrieval SHALL use page-local display formula order as a fallback when an explicit numbered formula label is missing from the preferred page text.

#### Scenario: Preferred page contains unlabeled second display formula
- **GIVEN** the user's current page contains multiple display-like formula lines
- **AND** the second display formula has no extracted `(2)` label
- **AND** explicit formula 2 matching fails on that page
- **WHEN** the user asks to explain formula 2
- **THEN** retrieved formula evidence targets the second display-like formula on that preferred page
- **AND** metadata marks the result as a formula order fallback

#### Scenario: Exact label remains preferred
- **GIVEN** the preferred page contains a formula explicitly labeled `(2)`
- **WHEN** the user asks to explain formula 2
- **THEN** retrieved formula evidence uses the explicit label match instead of order fallback

#### Scenario: No preferred page context
- **GIVEN** no preferred/current page is available
- **WHEN** explicit formula label matching fails
- **THEN** retrieval SHALL NOT infer formula number from global document formula order
