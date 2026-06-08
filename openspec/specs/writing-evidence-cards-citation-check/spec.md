# writing-evidence-cards-citation-check Specification

## Purpose
TBD - created by archiving change writing-evidence-cards-citation-check. Update Purpose after archive.
## Requirements
### Requirement: Writing projects expose normalized evidence cards

Writing projects with evidence metadata SHALL expose evidence cards that can be displayed in the writing UI.

#### Scenario: Research idea draft has local and external evidence

- **GIVEN** a writing project created from a research idea with `evidence_items`
- **WHEN** the client requests project evidence cards
- **THEN** the response includes each evidence item as a card
- **AND** each card includes title, role label, snippet, citation marker, and local/import status
- **AND** local paper identifiers are preserved when available

#### Scenario: Topic draft only has recommended local papers

- **GIVEN** a writing project created from a topic with `recommended_paper_ids`
- **WHEN** the client requests project evidence cards
- **THEN** local papers are returned as evidence cards
- **AND** the response reports coverage counts for local and external evidence

### Requirement: Writing sections can be checked for citation support

The system SHALL provide a section-level citation check that maps citations to evidence and reports support quality.

#### Scenario: Section contains bracket citations

- **GIVEN** a writing section with text containing `[1]`
- **AND** the writing project has an evidence card at index 1
- **WHEN** the client checks the section citations
- **THEN** the response includes a check result for `[1]`
- **AND** local papers are scored as strong, partial, or weak using existing support scoring

#### Scenario: Section references external-only evidence

- **GIVEN** a writing section cites evidence that is not imported into the local knowledge base
- **WHEN** the client checks the section citations
- **THEN** the response marks the citation as unchecked external evidence
- **AND** the explanation tells the user to import or supplement the paper before relying on it

#### Scenario: Section has no citations

- **GIVEN** a writing section with substantive text but no citation marker
- **WHEN** the client checks the section citations
- **THEN** the response reports missing citations
- **AND** recommends candidate evidence cards from the project

### Requirement: Writing UI surfaces evidence and diagnostics

The writing project UI SHALL show evidence cards and section citation diagnostics without disrupting editing.

#### Scenario: User opens a writing project

- **GIVEN** a user selects a writing project
- **WHEN** evidence cards are available
- **THEN** the UI shows a right-side evidence panel
- **AND** the user can copy a citation marker from a card

#### Scenario: User checks a section

- **GIVEN** a user is editing a section
- **WHEN** they click `校验引用`
- **THEN** the UI displays a diagnostic summary and per-citation explanations
- **AND** weak, missing, and external-only evidence are visually distinct

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

