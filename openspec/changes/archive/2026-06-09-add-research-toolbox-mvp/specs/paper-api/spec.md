## MODIFIED Requirements

### Requirement: Paper API exposes paper metadata
The paper API SHALL expose paper identity, bibliographic metadata, source metadata, processing state, import ownership, and shared importance marker metadata.

#### Scenario: Paper has linked toolbox entries
- **WHEN** a paper is linked to one or more toolbox entries
- **THEN** the paper detail workflow can retrieve the linked toolbox entries with relation labels and evidence notes

#### Scenario: Paper has no linked toolbox entries
- **WHEN** a paper has no toolbox links
- **THEN** the toolbox-link response returns an empty list without failing the paper detail workflow
