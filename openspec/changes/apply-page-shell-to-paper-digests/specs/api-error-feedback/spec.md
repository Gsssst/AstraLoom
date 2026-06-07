## ADDED Requirements

### Requirement: Paper Digest Inbox Shows Recovery Guidance

The paper digest inbox SHALL display structured recovery guidance when digest loading or paper-level digest actions fail.

#### Scenario: Digest loading fails
- **WHEN** the digest inbox cannot load digest history or unread counts
- **THEN** it displays a persistent failure message with recovery guidance and retryability metadata.

#### Scenario: Digest paper action fails
- **WHEN** ingesting a recommendation, updating reading status, marking digests read, or recording feedback fails
- **THEN** the page displays structured recovery guidance from the shared API error helper.
