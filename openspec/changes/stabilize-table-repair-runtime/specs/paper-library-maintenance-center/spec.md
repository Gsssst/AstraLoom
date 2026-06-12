## MODIFIED Requirements

### Requirement: Maintenance Center Supports Repair Actions
The maintenance center SHALL surface prioritized repair actions and let administrators run bounded maintenance jobs. Repair actions SHALL distinguish successful repairs from completed jobs that found only failures or skips.

#### Scenario: Recommendations are available
- **WHEN** maintenance recommendations are returned
- **THEN** the page shows severity, reason, sample papers, and the action button for each recommendation.

#### Scenario: Admin runs a repair action
- **WHEN** the admin triggers BM25 rebuild, embedding backfill, full-text backfill, or low-quality table repair
- **THEN** the page calls the corresponding maintenance endpoint and refreshes health after completion.

#### Scenario: Table repair completes without repaired papers
- **WHEN** the low-quality table repair job finishes with processed candidates but zero successful repairs
- **THEN** the maintenance center reports the job as completed with failures
- **AND** displays the actionable parser/runtime reason returned by the backend.
