## ADDED Requirements

### Requirement: Paper chat supports temporary PDF and image attachments
The paper-detail AI Q&A panel SHALL let users attach PDF and image files as temporary context for the next paper question.

#### Scenario: User attaches a file in paper chat
- **WHEN** a user selects a PDF or image file no larger than 50MB from the paper-detail AI Q&A composer
- **THEN** the panel shows a removable attachment chip and begins extraction

#### Scenario: User sends a paper question with attachments
- **WHEN** attachment extraction is complete and the user sends a paper-detail AI question
- **THEN** the request includes the open paper context plus extracted attachment context for the model

#### Scenario: User tries to send before extraction completes
- **WHEN** any paper-detail chat attachment is still extracting
- **THEN** the panel prevents sending and asks the user to wait

#### Scenario: User removes a paper chat attachment
- **WHEN** the user removes an attachment chip before sending
- **THEN** that attachment is not included in the next paper-detail AI question
