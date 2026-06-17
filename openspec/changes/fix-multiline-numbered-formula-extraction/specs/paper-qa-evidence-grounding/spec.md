## ADDED Requirements

### Requirement: Numbered formula extraction handles inline labels
Paper Q&A evidence routing SHALL find explicitly numbered formulas when extracted text places the parenthesized number inline with formula text or nearby prose.

#### Scenario: Formula number is followed by prose
- **WHEN** extracted paper text contains a math expression with `(2)` and additional prose on the same line
- **AND** the user asks about formula 2
- **THEN** retrieved evidence targets that formula expression

#### Scenario: No structured formula block exists
- **WHEN** structured formula evidence is unavailable but page text contains a numbered formula
- **AND** the user asks about that formula number
- **THEN** retrieved evidence includes the text-extracted numbered formula
