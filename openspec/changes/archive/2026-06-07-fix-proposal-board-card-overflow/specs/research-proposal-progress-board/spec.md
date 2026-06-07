## MODIFIED Requirements

### Requirement: Frontend Shows Proposal Progress Board
The research project page SHALL include a board view that groups Proposals by progress state and exposes next-step actions.

#### Scenario: User opens board tab
- **WHEN** the user opens the Proposal progress board
- **THEN** the page displays grouped columns with counts, priority scores, blockers, signals, and recommended actions
- **AND** dynamic card content including long titles, blocker messages, signals, and actions remains inside each Proposal card without horizontal overflow.

#### Scenario: User triggers recommended action
- **WHEN** the user selects a board card's recommended action
- **THEN** the page opens or invokes the existing relevant workflow without losing the current workbench state.

#### Scenario: Board load fails
- **WHEN** the board endpoint fails
- **THEN** the page uses existing API recovery guidance and leaves the existing Proposal list usable.
