## MODIFIED Requirements

### Requirement: Multimodal Evidence Routing
Paper Q&A SHALL prefer ready visual evidence alongside text/table evidence for figure, chart, architecture, method, and experiment questions.

#### Scenario: User asks about method diagram
- **GIVEN** a paper has extracted visual assets, OCR text, table crop markdown, or visual summaries marked ready
- **WHEN** the user asks about the method architecture, figure, chart, or experimental visualization
- **THEN** the retrieved evidence includes visual candidates before falling back to text-only evidence.

#### Scenario: User asks about experimental results
- **GIVEN** a paper has ready structured tables or visual table evidence
- **WHEN** the user asks about experimental results, experiment analysis, ablations, baselines, charts, or metrics in English or Chinese
- **THEN** the retrieved evidence uses the complete experiment evidence strategy and includes table packs, OCR-enhanced visual table markdown, captions, and page-aware context before general full-text chunks.

#### Scenario: Parser table evidence is low fidelity but visual OCR is available
- **GIVEN** a paper has low-fidelity structured table output and OCR-enhanced visual table markdown for the same page or table
- **WHEN** the user asks for experiment analysis or table-heavy conclusions
- **THEN** the answer context prefers the OCR-enhanced visual table markdown while preserving warnings for uncertain or low-confidence cells.
