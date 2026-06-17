## ADDED Requirements

### Requirement: PDF-extracted Unicode numbered formulas are retrieved exactly
Paper Q&A evidence retrieval SHALL recognize numbered formula labels in PDF-extracted Unicode math lines even when the label is adjacent to following section text.

#### Scenario: Formula label is followed by a section heading
- **GIVEN** page text contains `Q˜ =XW˜⊤, K˜ =XW˜⊤, (2) 3.3.TokenSelectorOptimization`
- **WHEN** the user asks to explain formula 2
- **THEN** retrieved formula evidence includes the `Q˜` and `K˜` expression
- **AND** metadata marks it as an exact formula number match

### Requirement: Page-local formula fallback excludes prose fragments
Paper Q&A evidence retrieval SHALL NOT count prose context lines as standalone display formulas for page-local formula order fallback.

#### Scenario: Context sentence ends with an equation setup
- **GIVEN** a preferred page contains a prose line `R ≪ D being the rank. Given the input sequence X =`
- **AND** the page also contains `Q˜ =XW˜⊤, K˜ =XW˜⊤, (2)`
- **WHEN** explicit matching is unavailable and the user asks for formula 2
- **THEN** page-local order fallback SHALL NOT return the prose line as formula 2

### Requirement: Formula retrieval handles one-page reader offsets
Paper Q&A evidence retrieval SHALL search a narrow page neighborhood for exact numbered formula labels when a preferred reading page is available.

#### Scenario: Extracted formula is one page after current reader page
- **GIVEN** current reading page is 3
- **AND** extracted page 4 contains formula `(2)`
- **WHEN** the user asks to explain formula 2
- **THEN** retrieval can use the exact page 4 formula evidence before falling back to page-local order on page 3
