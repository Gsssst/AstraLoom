## ADDED Requirements

### Requirement: Multiple numbered formulas are retrieved together
Paper Q&A evidence retrieval SHALL retrieve evidence for every explicitly requested formula number in one question.

#### Scenario: User asks for formulas 8, 9, and 10
- **GIVEN** page text contains formulas labeled `(8)`, `(9)`, and `(10)`
- **WHEN** the user asks `具体解释一下公式8、9、10`
- **THEN** formula evidence includes entries for 8, 9, and 10
- **AND** each entry records its own `requested_formula_number`

#### Scenario: Single formula behavior remains unchanged
- **GIVEN** page text contains formula `(9)`
- **WHEN** the user asks `解释公式9`
- **THEN** retrieval returns formula 9 evidence as before
