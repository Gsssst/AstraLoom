## ADDED Requirements

### Requirement: CVF OpenAccess conference discovery
The system SHALL provide a bounded CVF OpenAccess discovery adapter for official CVPR, ICCV, and ECCV venue-year paper requests.

#### Scenario: User requests CVPR papers for a published year
- **WHEN** a paper discovery workflow requests venue `CVPR` and a specific published year
- **THEN** the system searches the matching CVF OpenAccess proceedings page
- **AND** returns normalized paper candidates with official venue/year provenance.

#### Scenario: CVF page is unavailable or has no matching results
- **WHEN** the CVF OpenAccess adapter cannot fetch or parse the requested venue-year page
- **THEN** the system degrades to other scholarly providers
- **AND** marks venue membership as unconfirmed unless another trusted source confirms it.

### Requirement: Venue evidence has provider provenance
The system SHALL preserve the source of venue evidence when paper candidates are normalized, merged, enriched, or displayed.

#### Scenario: Venue comes from CVF
- **WHEN** a candidate is discovered on a CVF OpenAccess venue-year page
- **THEN** its metadata records venue provenance as `cvf_openaccess`
- **AND** downstream Research Scout cards can show the venue as verified by CVF.

#### Scenario: Venue comes from scholarly metadata
- **WHEN** venue information comes from Semantic Scholar or OpenAlex instead of CVF
- **THEN** its metadata records that provider as the venue provenance
- **AND** the system does not treat it as official CVF evidence unless it matches the requested venue.

### Requirement: Conference discovery can enrich PDF and citation metadata
The system SHALL enrich CVF-discovered candidates with arXiv, Semantic Scholar, or OpenAlex metadata when a safe title, DOI, or arXiv match is available.

#### Scenario: CVF candidate has an arXiv match
- **WHEN** a CVF-discovered candidate can be matched to an arXiv paper
- **THEN** the merged candidate preserves CVF venue evidence
- **AND** adds the arXiv ID and PDF URL.

#### Scenario: CVF candidate has no arXiv match
- **WHEN** no arXiv match is found for a CVF-discovered candidate
- **THEN** the candidate remains eligible with CVF source evidence
- **AND** the UI does not claim an arXiv PDF exists.
