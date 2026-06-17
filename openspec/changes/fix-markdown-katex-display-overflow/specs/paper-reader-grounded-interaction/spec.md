## ADDED Requirements

### Requirement: AI answer display equations remain readable in constrained chat widths
The paper reader SHALL render Markdown display equations in AI answers as intact horizontal math blocks when the chat panel width is constrained. Long equations SHALL remain readable via horizontal scrolling inside the answer bubble rather than being squeezed, clipped, or broken by prose wrapping rules.

#### Scenario: Long formula in a narrow paper chat answer
- **WHEN** a paper AI answer contains a KaTeX display equation wider than the available message bubble
- **THEN** the equation remains on a single readable math line
- **AND** the equation area can scroll horizontally inside the answer bubble

#### Scenario: Normal Markdown content remains unaffected
- **WHEN** a paper AI answer contains prose, inline math, tables, or code blocks
- **THEN** those elements keep their existing Markdown rendering behavior
