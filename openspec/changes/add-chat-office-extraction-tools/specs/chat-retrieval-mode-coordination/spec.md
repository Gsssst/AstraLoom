## ADDED Requirements

### Requirement: Chat attachments support Office documents
The shared chat attachment workflow SHALL accept and extract supported Office documents as bounded text context for chat turns.

#### Scenario: Upload Word document attachment
- **WHEN** a user attaches a `.docx` file in chat
- **THEN** the backend extracts bounded Word document text
- **AND** the text is included in the attachment context sent with the chat turn

#### Scenario: Upload PowerPoint document attachment
- **WHEN** a user attaches a `.pptx` file in chat
- **THEN** the backend extracts bounded slide text grouped by slide
- **AND** the text is included in the attachment context sent with the chat turn

#### Scenario: Legacy Office format is unsupported
- **WHEN** a user attaches a `.doc` or `.ppt` file that cannot be safely parsed
- **THEN** the backend rejects the extraction with a clear message asking for `.docx` or `.pptx`

#### Scenario: Attachment picker advertises supported Office files
- **WHEN** the user opens the shared chat attachment picker
- **THEN** the accepted file types include PDF, images, DOCX, and PPTX
