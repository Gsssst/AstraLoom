## ADDED Requirements

### Requirement: Paper detail toolbar handles long titles
The paper detail toolbar SHALL keep navigation, title, reading status, PDF controls, importance controls, and favorite controls visible and non-overlapping when the paper title is long.

#### Scenario: Long title on desktop
- **WHEN** a paper detail page displays a long title on a desktop-width viewport
- **THEN** the title is truncated with ellipsis before it overlaps action controls
- **AND** the reading status and favorite controls remain fully visible.

#### Scenario: Narrow toolbar width
- **WHEN** the paper detail toolbar does not have enough horizontal space for all actions
- **THEN** action groups may wrap within the toolbar
- **AND** no action button is clipped by the viewport edge.
