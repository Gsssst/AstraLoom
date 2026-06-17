## ADDED Requirements

### Requirement: PDF reader supports global gesture zoom
The paper PDF reader SHALL support global zoom for enhanced PDF rendering so users can enlarge or shrink the whole rendered page using familiar PDF viewer interactions.

#### Scenario: User zooms with touchpad pinch or modifier wheel
- **WHEN** the enhanced PDF reader is rendering pages and the user performs a touchpad pinch or Ctrl/Cmd + mouse wheel gesture over the PDF pane
- **THEN** the reader changes the rendered PDF page zoom level
- **AND** the browser page itself does not zoom.

#### Scenario: User zooms with toolbar controls
- **WHEN** the enhanced PDF reader is rendering pages and the user clicks zoom in, zoom out, or fit-to-width controls
- **THEN** the reader updates the rendered PDF page size
- **AND** shows the current zoom percentage.

#### Scenario: Zoom preserves reading context
- **WHEN** the user changes zoom while reading a page
- **THEN** the reader keeps the cursor-centered or viewport-centered reading position visible as much as possible
- **AND** page tracking continues to update from scrolling.

#### Scenario: Evidence-aware reading still works after zoom
- **WHEN** the PDF reader is zoomed and the user selects text or clicks an evidence citation jump
- **THEN** text selection, evidence highlighting, and page navigation continue to work on the rendered PDF text layer.

#### Scenario: Native PDF fallback is active
- **WHEN** the PDF reader is in native fallback mode
- **THEN** app-controlled zoom controls are disabled or unavailable
- **AND** the fallback still provides the direct PDF preview/opening path.
