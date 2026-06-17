## ADDED Requirements

### Requirement: Stacked summation formulas preserve bounds and averaging context
Paper Q&A evidence retrieval SHALL include stacked summation and fraction fragments around numbered formulas when PDF text extraction splits a rendered formula across neighboring lines.

#### Scenario: Formula 11 is split across summation fragments
- **GIVEN** page text contains `1 (cid:88)`, `L= (S(i)-S∗(i))2. (11)`, `N`, and `i=1` around the same rendered formula
- **WHEN** the user asks to explain formula 11
- **THEN** formula evidence includes the loss term, the averaging factor, and summation bounds
- **AND** the evidence includes a normalized one-line formula representation

### Requirement: Formula fragments are not treated as section headings
Paper Q&A evidence retrieval SHALL NOT treat short math fragments as numbered section headings.

#### Scenario: Summation fragment resembles a numbered heading
- **GIVEN** extracted text contains `1 (cid:88)`
- **WHEN** retrieving numbered formula evidence
- **THEN** the evidence metadata SHALL NOT set `matched_heading` to `1 (cid:88)`
