## ADDED Requirements

### Requirement: PDF gesture zoom remains visually continuous
The paper PDF reader SHALL keep the currently rendered PDF content visible while users change zoom through toolbar controls, touchpad pinch, or Ctrl/Cmd + wheel gestures.

#### Scenario: User performs repeated zoom gestures
- **WHEN** the enhanced PDF reader is rendering pages and the user repeatedly zooms with touchpad pinch or Ctrl/Cmd + wheel
- **THEN** the visible PDF pages scale continuously without flashing to a blank white page between gesture steps.

#### Scenario: Scaled pages keep readable layout
- **WHEN** the user zooms beyond fit-to-width
- **THEN** the PDF pane reserves the scaled page width and height
- **AND** users can scroll vertically and horizontally without pages overlapping.

#### Scenario: Evidence jumps after zoom
- **WHEN** the user clicks an evidence citation after zooming
- **THEN** the highlighted evidence is scrolled into the visible PDF pane using the transformed on-screen position.
