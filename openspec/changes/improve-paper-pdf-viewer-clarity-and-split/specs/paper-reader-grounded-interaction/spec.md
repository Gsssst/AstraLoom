## ADDED Requirements

### Requirement: PDF zoom renders pages clearly
The paper PDF reader SHALL render enhanced PDF pages at the active zoom size instead of enlarging a lower-resolution rendered canvas with a post-render CSS transform.

#### Scenario: User zooms in on small text or formulas
- **WHEN** the enhanced PDF reader is displaying a page and the user increases zoom above fit-to-width
- **THEN** the PDF page canvas, text layer, and annotation layer are rendered at the effective zoomed width
- **AND** the reader does not rely on CSS transform scaling as the primary zoom mechanism.

#### Scenario: User changes zoom with controls or gesture
- **WHEN** the user clicks toolbar zoom controls or uses Ctrl/Cmd + wheel over the enhanced PDF pane
- **THEN** the zoom level changes in larger readable increments
- **AND** the current reading position remains visible as much as practical.

### Requirement: Paper AI split supports wider chat reading
The paper detail PDF/chat split SHALL allow the AI Q&A panel to be resized wide enough for long grounded answers while preserving the PDF panel and the collapsed chat rail behavior.

#### Scenario: User drags the split toward the PDF side
- **WHEN** the user drags the PDF/chat divider left on a desktop viewport
- **THEN** the PDF panel can shrink to about 30% of the workspace
- **AND** the AI Q&A panel can expand to use most of the remaining width.

#### Scenario: User drags the split toward chat collapse
- **WHEN** the user drags the divider far enough toward the right edge
- **THEN** the existing chat rail collapse behavior remains available.
