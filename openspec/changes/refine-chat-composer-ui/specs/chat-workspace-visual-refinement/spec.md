## ADDED Requirements

### Requirement: Chat composer controls are visually polished
The chat page SHALL present upload, input, send, prompt shortcut, and attachment controls with consistent sizing, spacing, focus, hover, and disabled states.

#### Scenario: User focuses the chat input
- **WHEN** the chat textarea receives focus
- **THEN** the composer shows a clear focused state without resizing or shifting controls

#### Scenario: User attaches files
- **WHEN** one or more files are attached
- **THEN** attachments are displayed as compact chips with stable thumbnails, filenames, status, and remove controls

#### Scenario: User uses mobile chat
- **WHEN** the chat page is shown on a narrow viewport
- **THEN** upload, input, and send controls remain aligned and usable without overlapping
