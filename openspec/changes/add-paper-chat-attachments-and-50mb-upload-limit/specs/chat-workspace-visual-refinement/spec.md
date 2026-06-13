## ADDED Requirements

### Requirement: Chat attachments accept larger research files
The chat workspace SHALL accept PDF and image attachments up to 50MB per file for temporary question context.

#### Scenario: User attaches a large research PDF
- **WHEN** a user selects a PDF or image file no larger than 50MB
- **THEN** the chat workspace accepts the file and begins extraction for use in the next message

#### Scenario: User attaches an oversized file
- **WHEN** a user selects a PDF or image file larger than 50MB
- **THEN** the chat workspace rejects the file with a clear size warning
