## MODIFIED Requirements

### Requirement: Maintenance Actions
The paper library SHALL expose maintenance actions for missing or failed processing states and SHALL report queued/running/success/failed status for long-running actions.

#### Scenario: Visual evidence extraction is started for one paper
- **WHEN** an admin starts the "提取视觉证据" action on a paper
- **THEN** the action returns a pollable job id and the current visual evidence status without waiting for all OCR calls.

#### Scenario: Visual evidence job finishes
- **WHEN** the single-paper visual evidence job finishes
- **THEN** the paper list/detail status reflects ready visual evidence on success or the stored failure reason on failure.
