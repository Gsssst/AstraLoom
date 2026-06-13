## MODIFIED Requirements

### Requirement: Maintenance Actions
The paper library SHALL expose maintenance actions for missing or failed processing states and SHALL report queued/running/success/failed status for long-running actions.

#### Scenario: Visual evidence extraction is running
- **WHEN** a visual evidence extraction job is queued or running from a paper action
- **THEN** the paper processing area displays visible progress, current paper information when available, and the latest job message.

#### Scenario: Visual evidence is ready but table OCR is incomplete
- **WHEN** a paper has ready visual evidence with missing table OCR, missing summaries, failed status, or low-confidence visual tables
- **THEN** the maintenance center treats the paper as needing visual evidence refresh and exposes a visual evidence extraction action.

#### Scenario: Visual evidence extraction finishes without meaningful count totals
- **WHEN** a visual evidence extraction job finishes with zero success, failure, and skipped counts but includes a message
- **THEN** the completion feedback displays the job message instead of a `成功 0，失败 0，跳过 0` summary.
