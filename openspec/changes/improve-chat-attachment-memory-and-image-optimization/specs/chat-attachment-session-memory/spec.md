## ADDED Requirements

### Requirement: Chat attachments persist for follow-up turns
The system SHALL retain temporary attachment context in the current chat surface after a successful send so follow-up questions can reuse the same uploaded PDF or image without re-uploading it.

#### Scenario: User sends a question with an uploaded PDF
- **WHEN** a user sends a chat question with a ready PDF attachment
- **THEN** later follow-up questions in the same chat surface include the PDF extracted text unless the user removes the remembered attachment

#### Scenario: User sends a question with an uploaded image
- **WHEN** a user sends a chat question with a ready image attachment
- **THEN** later follow-up questions in the same chat surface include the image attachment payload unless the user removes the remembered attachment

#### Scenario: User removes remembered attachment
- **WHEN** a user removes a remembered attachment chip
- **THEN** future questions no longer include that attachment context

#### Scenario: User adds a new attachment after memory exists
- **WHEN** a user adds new current-turn attachments while remembered attachments exist
- **THEN** the next question includes both remembered and new ready attachments without duplicating the same attachment
