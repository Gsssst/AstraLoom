## ADDED Requirements

### Requirement: PDF layout resizing preserves visible pages
The paper reader SHALL keep already-rendered PDF pages visible while a user actively drags the desktop split handle between the PDF reader and AI Q&A, or while the surrounding desktop app layout is resizing. The reader SHALL defer PDF page width recalculation until the resize interaction settles, so the PDF area does not turn blank during the resize.

#### Scenario: User drags the PDF and AI Q&A split handle
- **WHEN** a user drags the desktop split handle between the PDF reader and AI Q&A
- **THEN** the PDF reader keeps the existing rendered pages visible during the drag
- **AND** the PDF page width is recalculated after the drag ends

#### Scenario: User expands the desktop sidebar while reading a PDF
- **WHEN** the desktop navigation sidebar expands or collapses while the PDF reader is visible
- **THEN** the PDF reader keeps the existing rendered pages visible during the layout transition
- **AND** the PDF page width is recalculated after the layout width settles

#### Scenario: User uses other PDF interactions after resizing
- **WHEN** a user finishes resizing the PDF workspace
- **THEN** page jumping, evidence navigation, PDF text selection, and zoom controls remain usable
