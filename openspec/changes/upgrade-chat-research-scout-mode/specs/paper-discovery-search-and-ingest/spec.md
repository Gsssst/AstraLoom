## ADDED Requirements

### Requirement: Chat can consume comprehensive scholarly discovery
The paper discovery service SHALL provide normalized scholarly candidates that chat can consume without requiring users to leave the conversation first.

#### Scenario: Research Scout asks for comprehensive candidates
- **WHEN** chat invokes scholarly discovery for Research Scout mode
- **THEN** the service queries the comprehensive provider set, deduplicates equivalent works, and returns normalized candidates.

#### Scenario: Candidate has a source URL
- **WHEN** a scholarly candidate includes a source URL or PDF URL
- **THEN** chat metadata preserves those URLs so the frontend can offer source inspection.
