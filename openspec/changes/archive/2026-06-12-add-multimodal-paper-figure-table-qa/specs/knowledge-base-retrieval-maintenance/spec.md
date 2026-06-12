## ADDED Requirements

### Requirement: Visual Evidence Maintenance Visibility
Administrators SHALL be able to inspect whether papers have visual assets and visual summaries available for multimodal Q&A.

#### Scenario: Admin views visual evidence maintenance health
- **WHEN** an administrator opens the knowledge-base maintenance console
- **THEN** the system displays counts or recommendations for papers missing visual assets and papers missing visual summaries.

### Requirement: Bounded Visual Evidence Maintenance Actions
Administrators SHALL be able to extract visual assets and summarize visual evidence in bounded batches.

#### Scenario: Admin backfills visual evidence
- **WHEN** an administrator triggers visual asset extraction or visual summary backfill
- **THEN** the operation runs with a bounded limit
- **AND** returns processed, success, failed, skipped counts, and actionable errors.
