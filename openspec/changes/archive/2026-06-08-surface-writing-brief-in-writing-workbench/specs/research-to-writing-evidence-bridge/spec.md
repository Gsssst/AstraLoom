## ADDED Requirements

### Requirement: Writing Workbench Surfaces Preserved Proposal Brief
The Writing workbench SHALL surface a preserved Proposal writing brief when the selected writing project metadata contains one.

#### Scenario: Research-derived writing project has a saved brief
- **WHEN** the user opens a Writing project whose metadata includes `writing_brief`
- **THEN** the workbench displays a writing-brief panel with title candidates, abstract draft, contribution chain, section outline, claim-evidence map, unsafe claims, and evidence gaps.

#### Scenario: Writing project has no saved brief
- **WHEN** the user opens a Writing project without `writing_brief` metadata
- **THEN** the workbench remains usable without showing a broken writing-brief panel.

### Requirement: Writing Brief Risks Affect Workbench Guidance
The Writing workbench SHALL include preserved unsafe claims and unsupported claim-evidence items in the visible next-action and blocker guidance.

#### Scenario: Brief contains unsafe claims
- **WHEN** the selected writing project has unsafe claims in its saved writing brief
- **THEN** the workbench shows a warning or blocker that routes the user toward evidence/citation review before polishing or export.

#### Scenario: Brief contains only supported claims
- **WHEN** the saved writing brief contains supported claims and no unsafe claims
- **THEN** the workbench shows the brief as ready for drafting without adding a high-risk blocker.

### Requirement: Writing Brief Actions Reuse Existing Workbench Tools
The Writing workbench SHALL provide lightweight actions for copied brief content and navigation to existing writing tools.

#### Scenario: User wants to reuse brief content
- **WHEN** the user clicks copy actions for title candidates, abstract draft, contribution claims, or citation markers
- **THEN** the selected text is copied without changing the draft content unexpectedly.

#### Scenario: User wants to resolve an unsupported claim
- **WHEN** the user uses the action for an unsupported or unsafe claim
- **THEN** the workbench routes the user to the evidence or citation-check surface rather than silently accepting the claim.
