## ADDED Requirements

### Requirement: PDF zoom avoids continuous white flashing
The paper PDF reader SHALL avoid repeated blank or white page flashes during continuous enhanced-reader zoom gestures while preserving sharp rendered pages after zoom settles.

#### Scenario: User pinch-zooms continuously
- **WHEN** the enhanced PDF reader is rendering pages and the user performs a continuous touchpad pinch or Ctrl/Cmd + wheel zoom gesture
- **THEN** the visible page scales immediately without forcing a high-resolution PDF canvas re-render for every gesture tick
- **AND** the page does not repeatedly disappear into a blank white repaint state.

#### Scenario: Zoom input settles
- **WHEN** the user stops changing the zoom level for a short idle interval
- **THEN** the reader re-renders the PDF canvas, text layer, and annotation layer at the active zoomed width
- **AND** the final settled page remains sharp rather than relying on permanent CSS-only scaling.

#### Scenario: User uses toolbar zoom controls
- **WHEN** the user clicks zoom in, zoom out, or fit-to-width controls
- **THEN** the reader gives immediate visual feedback
- **AND** settles to a high-resolution rendered PDF page.
