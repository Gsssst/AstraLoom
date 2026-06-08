## ADDED Requirements

### Requirement: Section citation checks include claim safety diagnostics
The system SHALL return claim-level safety diagnostics when checking a writing section for citation support.

#### Scenario: Section contains uncited substantive claims
- **WHEN** a section contains substantive claim sentences without bracket citations
- **THEN** the citation check response includes claim diagnostics marking those claims as missing citations
- **AND** the response summary counts missing-citation claims.

#### Scenario: Section contains cited claims with weak support
- **WHEN** a cited claim maps to a local evidence card but the support score is weak
- **THEN** the claim diagnostic marks the claim as weakly supported and includes a next action to strengthen or replace the citation.

#### Scenario: Section cites external-only evidence
- **WHEN** a claim cites an evidence card that is not imported into the local knowledge base
- **THEN** the claim diagnostic marks the claim as unchecked external evidence and recommends importing or supplementing the paper.

### Requirement: Writing UI surfaces claim safety diagnostics
The Writing UI SHALL display claim safety diagnostics in the section editor after a citation check.

#### Scenario: User checks section citations
- **WHEN** claim safety diagnostics are returned
- **THEN** the section editor shows a safety summary with missing, weak, and unchecked claim counts
- **AND** each risky claim is visible with its status and recommended action.

#### Scenario: Section has no risky claims
- **WHEN** all detected cited claims are strongly or partially supported and no uncited claim is detected
- **THEN** the section editor shows a low-risk safety status without hiding existing citation-level details.
