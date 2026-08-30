## ADDED Requirements

### Requirement: Desktop paper split supports bidirectional snap collapse
The desktop paper reader SHALL collapse either the AI Q&A panel or the PDF panel into a narrow restorable rail when the user drags the divider beyond the corresponding edge threshold. The remaining expanded panel SHALL fill all workspace width not occupied by the divider and collapsed rail.

#### Scenario: User prioritizes PDF reading
- **WHEN** the user drags the PDF/AI divider beyond the AI collapse threshold near the right edge
- **THEN** AI Q&A collapses into a narrow rail
- **AND** the PDF reader fills the remaining workspace width

#### Scenario: User prioritizes AI analysis
- **WHEN** the user drags the PDF/AI divider beyond the PDF collapse threshold near the left edge
- **THEN** the PDF reader collapses into a narrow rail
- **AND** AI Q&A fills the remaining workspace width

#### Scenario: User restores a collapsed panel
- **WHEN** the user activates the restore control on either collapsed rail
- **THEN** both panels return to the normal desktop split
- **AND** existing PDF reading and AI conversation state remain available

#### Scenario: User drags back from a collapsed rail
- **WHEN** the user drags the divider away from a collapsed edge and back into the normal split range
- **THEN** the collapsed panel reopens
- **AND** the divider follows the bounded normal split width
