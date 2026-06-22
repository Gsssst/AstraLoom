## ADDED Requirements

### Requirement: User model preference fields
The user model SHALL persist optional LLM provider and model preference fields for each user.

#### Scenario: Existing users after migration
- **WHEN** the user model preference migration is applied
- **THEN** existing user rows retain their existing account data
- **AND** their LLM provider/model preference fields are null until they save a preference

#### Scenario: User saves model preference
- **WHEN** a user saves an LLM provider/model preference
- **THEN** the provider and model values are stored on that user's record
- **AND** other users' records are not modified
