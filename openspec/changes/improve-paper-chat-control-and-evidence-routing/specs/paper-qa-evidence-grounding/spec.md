## ADDED Requirements

### Requirement: Formula-number questions target numbered formulas
Paper Q&A evidence routing SHALL recognize explicit formula number or ordinal formula requests and prioritize matching formula evidence.

#### Scenario: User asks about formula 1
- **WHEN** structured formula evidence includes a numbered or labelled formula 1
- **AND** the user asks what formula 1 means
- **THEN** retrieved evidence includes that numbered formula before generic prose chunks

#### Scenario: Numbered formula is unavailable
- **WHEN** the user asks about a formula number that is not available in parsed formula evidence
- **THEN** the system falls back to formula-like evidence and records a formula limitation instead of treating the first prose expression as the target formula

### Requirement: Dataset questions prioritize experiment evidence
Paper Q&A evidence routing SHALL recognize dataset and benchmark questions and retrieve experiment, table, and caption evidence before generic document chunks.

#### Scenario: User asks which datasets are used
- **WHEN** the paper has experiment tables, captions, or text mentioning datasets/benchmarks
- **THEN** retrieved evidence includes those experiment/table/caption blocks so the answer can list dataset names and usage

### Requirement: Novelty questions include method and experiment evidence
Paper Q&A evidence routing SHALL recognize novelty or innovation evaluation questions and retrieve method, experiment, ablation, table, and limitation evidence together.

#### Scenario: User asks whether the paper is innovative
- **WHEN** the paper has method descriptions and experiment or ablation evidence
- **THEN** retrieved evidence includes both method and experiment/ablation evidence so the answer can evaluate novelty from method, experiment, and problem-setting angles
