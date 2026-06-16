## MODIFIED Requirements

### Requirement: Research Scout respects requested final answer candidate count
Research Scout final-answer context SHALL include candidate metadata for the requested final result count when that many ranked candidates are available, subject to the configured maximum final-result cap.

#### Scenario: Ten-paper request exposes ten candidate blocks
- **WHEN** a Research Scout request asks for ten papers and the backend has ten ranked candidates
- **THEN** the final answer context includes ten numbered candidate paper blocks
- **AND** the context diagnostics state how many ranked candidates exist and how many were included

#### Scenario: Genuine shortage is reported as underfilled
- **WHEN** Research Scout has fewer ranked candidates than the requested final result count
- **THEN** the final answer context includes all available candidate blocks
- **AND** retrieval diagnostics identify the result set as underfilled rather than implying an arbitrary context cap
