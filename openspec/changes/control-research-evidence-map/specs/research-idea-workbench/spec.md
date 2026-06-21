## ADDED Requirements

### Requirement: Evidence Map controls before proposal generation
The research idea workbench SHALL allow users to control the Evidence Map used for Gap Map extraction and proposal generation.

#### Scenario: Preview with evidence controls
- **WHEN** a project editor starts an Evidence Map or Gap Map preview with evidence controls
- **THEN** the run config persists the normalized controls
- **AND** the stored Evidence Map reflects pinned papers, excluded papers, and the configured evidence count limit
- **AND** the system preserves the current default behavior when no controls are provided

#### Scenario: Continue generation with revised evidence controls
- **WHEN** a project editor continues proposal generation from a reviewed Gap Map with revised evidence controls
- **THEN** the backend reapplies those controls to the run Evidence Map before candidate generation
- **AND** generated candidates, Gap Map references, and selected proposals use the controlled evidence set

#### Scenario: Excluded evidence is not used
- **WHEN** an evidence paper ID is marked as excluded
- **THEN** it is removed from every Evidence Map category before generation
- **AND** excluded evidence does not appear in candidate evidence references unless the user removes the exclusion and reruns preview or continuation

#### Scenario: Pinned evidence is prioritized
- **WHEN** evidence paper IDs are pinned and available in the collected Evidence Map
- **THEN** pinned items are retained ahead of non-pinned items within the configured evidence count limit
- **AND** the Evidence Map records a control summary explaining how many items were pinned, excluded, and retained

#### Scenario: User steers Evidence Map from the interface
- **WHEN** a user opens the Evidence Map tab
- **THEN** the interface exposes controls for evidence count, pinning, excluding, clearing pins, and clearing exclusions
- **AND** subsequent preview or continuation requests include the selected Evidence Map controls
