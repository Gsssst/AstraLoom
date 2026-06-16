## ADDED Requirements

### Requirement: Paper chat displays targeted section confidence
The paper-detail chat UI SHALL display exact targeted section hits as section-matched evidence rather than low generic coverage.

#### Scenario: Streamed answer has a matched numbered section
- **WHEN** streamed paper chat metadata indicates a matched requested section
- **THEN** the answer evidence panel shows a targeted section confidence label
- **AND** it does not show the answer as only partially supported because there is one section evidence reference

#### Scenario: Answer lacks section match metadata
- **WHEN** a paper chat answer has no targeted section match metadata
- **THEN** the evidence panel uses the existing generic evidence-count confidence behavior
