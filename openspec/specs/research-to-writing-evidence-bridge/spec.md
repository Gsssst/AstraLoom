# research-to-writing-evidence-bridge Specification

## Purpose
TBD - created by archiving change research-to-writing-evidence-bridge. Update Purpose after archive.
## Requirements
### Requirement: Convert Research Idea To Writing Draft
The system SHALL allow an authenticated user to create a writing project from an owned research Idea using a previewable writing brief when available.

#### Scenario: Create draft from evidence-backed Idea
- **WHEN** the user requests a writing draft from an owned Idea with evidence
- **THEN** the system creates a writing project containing Idea context, writing brief, evidence table, research gaps, claim-evidence map, and references.

#### Scenario: Create draft from Idea with weak evidence
- **WHEN** the Idea has no local evidence papers
- **THEN** the system still creates a writing project and marks the evidence status as insufficient.

#### Scenario: Create draft after writing brief preview
- **WHEN** the user creates a writing draft after previewing a Proposal writing brief
- **THEN** the created Writing project metadata includes the same bounded brief fields used for preview.

### Requirement: Preserve Evidence Metadata
The system SHALL preserve source project, source Idea, writing brief, claim-evidence map, and evidence paper metadata in the writing project.

#### Scenario: Metadata stored on writing project
- **WHEN** a writing project is created from a research Idea
- **THEN** project metadata includes source project ID, source Idea ID, writing brief, evidence items, and local paper IDs where available.

#### Scenario: Unsupported claims are preserved
- **WHEN** the writing brief marks claims as unsupported or unsafe
- **THEN** project metadata preserves those unsafe claims so the Writing UI can warn before polishing or citation insertion.

### Requirement: Navigate To Created Writing Project
The frontend SHALL navigate users from a research Idea to the newly created writing project.

#### Scenario: Open created draft
- **WHEN** the user clicks "生成写作草稿" on a Proposal
- **THEN** the frontend calls the bridge endpoint and opens the writing page with the created project selected.

### Requirement: Proposal Writing Brief Is Previewable
The system SHALL let an authenticated owner preview a bounded writing brief for a Proposal before creating a Writing project.

#### Scenario: Preview writing brief for owned Proposal
- **WHEN** the owner requests a writing brief for a Proposal
- **THEN** the response includes title candidates, abstract draft, contribution chain, section outline, claim-evidence map, evidence gaps, experiment writing plan, limitations, unsafe claims, and evidence status.

#### Scenario: Preview writing brief with sparse evidence
- **WHEN** the Proposal has no evidence items or local papers
- **THEN** the response still includes a draft scaffold and marks evidence status as insufficient with unsafe claims.

### Requirement: Proposal Writing Brief Uses Conservative Citation Grounding
The system SHALL generate writing brief evidence references only from evidence already attached to the Proposal.

#### Scenario: Claim has attached evidence
- **WHEN** a Proposal claim can be associated with existing evidence items
- **THEN** the writing brief maps the claim to those evidence references and marks the claim as supported or partially supported.

#### Scenario: Claim lacks attached evidence
- **WHEN** a Proposal claim has no attached evidence
- **THEN** the writing brief marks the claim as unsupported instead of inventing a citation.

### Requirement: Frontend Shows Writing Preparation Before Draft Creation
The research project page SHALL show writing preparation guidance for a Proposal before or alongside the create-draft action.

#### Scenario: User opens writing preparation panel
- **WHEN** the user opens or refreshes writing preparation for a Proposal
- **THEN** the page displays the brief summary, title candidates, outline, claim-evidence status, unsafe claims, and draft creation action.

#### Scenario: Writing brief load fails
- **WHEN** the writing brief endpoint fails
- **THEN** the page uses existing API recovery guidance and keeps the Proposal detail usable.

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

