## MODIFIED Requirements

### Requirement: Evidence-Backed Paper Q&A

Paper-page AI Q&A SHALL provide structured evidence references for current-paper answers whenever relevant chunks, tables, formulas, or ready visual evidence are available.

#### Scenario: Formula evidence is available

- **GIVEN** a paper has parsed structured formula or equation evidence
- **WHEN** the user asks about formulas, equations, symbols, objectives, or derivations
- **THEN** retrieved evidence includes relevant formula evidence before relying only on surrounding text chunks
- **AND** evidence metadata identifies the evidence type as formula and includes page metadata when available.

#### Scenario: Numbered section explanation needs equations

- **GIVEN** the user asks to explain a numbered section
- **AND** structured formula evidence is available near the matched section or page
- **WHEN** the AI builds its answer context
- **THEN** the numbered-section evidence remains primary
- **AND** relevant formula evidence is included as supplemental evidence.

### Requirement: Evidence Insufficiency Disclosure

Paper Q&A SHALL clearly disclose when evidence is insufficient, and SHALL scope that disclosure to the missing detail rather than implying the entire answer is unreliable when partial evidence exists.

#### Scenario: Formula details are missing but text evidence exists

- **GIVEN** a paper answer has current-paper text evidence
- **AND** the user asks about formulas or a section containing formulas
- **AND** no matching formula evidence is available
- **WHEN** the AI builds its answer context
- **THEN** the system prompt instructs the model to state that the specific formula or symbol detail was not retrieved
- **AND** the model is instructed to continue answering from the available text evidence without presenting the method as broadly unsupported.
