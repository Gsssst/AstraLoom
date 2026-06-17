## ADDED Requirements

### Requirement: Local PDF Magnifier
The paper PDF reader SHALL provide a toggleable local magnifier for enhanced PDF rendering so users can inspect small text or figure details without changing the global page scale.

#### Scenario: User inspects small PDF text
- **WHEN** the enhanced PDF reader is rendering pages and the user enables the magnifier
- **THEN** moving the pointer over a PDF page displays a local magnified view centered around the pointer
- **AND** the PDF page scale, current page, and scroll position remain unchanged.

#### Scenario: User disables magnification
- **WHEN** the magnifier is disabled or the pointer leaves the PDF page
- **THEN** the local magnified view is hidden
- **AND** text selection and evidence highlighting continue to work normally.

#### Scenario: Native PDF fallback is active
- **WHEN** the PDF reader is in native fallback mode
- **THEN** the local magnifier control is disabled or unavailable.
