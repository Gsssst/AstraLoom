## ADDED Requirements

### Requirement: Numbered formula retrieval prefers explicit formula labels
Paper Q&A evidence routing SHALL prefer explicitly numbered formulas from extracted paper text over unlabelled inline math or ordinal formula fallback.

#### Scenario: Inline math appears before formula 1
- **WHEN** extracted text contains inline math in an earlier section
- **AND** a later display formula is explicitly labelled `(1)`
- **AND** the user asks about formula 1
- **THEN** retrieved evidence targets the labelled formula `(1)` instead of the earlier inline math

#### Scenario: Explicit numbered formula is unavailable
- **WHEN** no extracted text or structured formula evidence explicitly matches the requested formula number
- **THEN** the system may fall back to ordered structured formula evidence and mark it as an order-based match
