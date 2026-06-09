## ADDED Requirements

### Requirement: Research workflow panels use shared quality algorithms
The research workbench panels SHALL use shared algorithms for citation keys, metadata quality, duplicate risk, evidence confidence, and graph edge strength instead of page-local ad hoc logic.

#### Scenario: Paper quality is displayed
- **WHEN** a paper library item or paper detail readiness panel is rendered
- **THEN** citation key and metadata quality values come from the shared research algorithm module

#### Scenario: Duplicate risk is displayed
- **WHEN** local paper results contain matching DOI, arXiv ID, or normalized titles
- **THEN** the duplicate risk result comes from the shared duplicate detection algorithm

#### Scenario: Evidence confidence is displayed
- **WHEN** a paper chat answer includes references or evidence metadata
- **THEN** the evidence confidence status comes from the shared evidence confidence algorithm

#### Scenario: Knowledge graph edges are rendered
- **WHEN** a knowledge graph edge is derived from evidence, citation, or proposal relationships
- **THEN** edge strength is assigned by the shared graph edge scoring algorithm where relationship metadata is available
